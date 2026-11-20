import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


DATABASE_PATH = Path(
    os.environ.get(
        "AICARE_DATABASE_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "aicare.sqlite3"),
    )
)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS family_members (
                id TEXT PRIMARY KEY,
                family_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                invite_code TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS patients (
                family_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS diary_records (
                family_id TEXT NOT NULL,
                record_date TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (family_id, record_date)
            );

            CREATE TABLE IF NOT EXISTS invites (
                family_id TEXT NOT NULL,
                invite_id TEXT NOT NULL,
                code TEXT NOT NULL COLLATE NOCASE UNIQUE,
                payload TEXT NOT NULL,
                PRIMARY KEY (family_id, invite_id)
            );

            CREATE TABLE IF NOT EXISTS medications (
                family_id TEXT NOT NULL,
                medication_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (family_id, medication_id)
            );

            CREATE TABLE IF NOT EXISTS dose_records (
                family_id TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (family_id, record_id)
            );

            CREATE TABLE IF NOT EXISTS inventory_movements (
                family_id TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (family_id, record_id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES family_members(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            );
            """
        )
        _migrate_legacy_users(connection)
        _migrate_legacy_sessions(connection)
        _migrate_legacy_records(connection)
        connection.execute("DROP TABLE IF EXISTS users")
        connection.execute("DROP TABLE IF EXISTS records")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS invites_family_id ON invites (family_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS medications_family_id "
            "ON medications (family_id)"
        )
        connection.commit()
        connection.execute("PRAGMA foreign_keys = ON")


def _migrate_legacy_users(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "users"):
        return
    connection.execute(
        """
        INSERT OR IGNORE INTO family_members
            (id, family_id, name, email, password_hash, role, invite_code,
             created_at)
        SELECT id, family_id, name, email, password_hash, role, invite_code,
               created_at
        FROM users
        """
    )


def _migrate_legacy_sessions(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = 'sessions'
        """
    ).fetchone()
    if not row:
        connection.execute(
            """
            CREATE TABLE sessions (
                token_hash TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES family_members(id)
                    ON DELETE CASCADE,
                expires_at TEXT NOT NULL
            )
            """
        )
        return
    if "REFERENCES USERS" not in (row["sql"] or "").upper():
        return

    connection.execute("DROP TABLE IF EXISTS sessions_migrated")
    connection.execute(
        """
        CREATE TABLE sessions_migrated (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES family_members(id)
                ON DELETE CASCADE,
            expires_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO sessions_migrated
            (token_hash, user_id, expires_at)
        SELECT token_hash, user_id, expires_at FROM sessions
        """
    )
    connection.execute("DROP TABLE sessions")
    connection.execute(
        "ALTER TABLE sessions_migrated RENAME TO sessions"
    )


def _migrate_legacy_records(connection: sqlite3.Connection) -> None:
    if not _table_exists(connection, "records"):
        return
    rows = connection.execute(
        """
        SELECT family_id, collection, record_id, payload
        FROM records
        ORDER BY rowid
        """
    ).fetchall()
    for row in rows:
        family_id = row["family_id"]
        record_id = row["record_id"]
        payload = row["payload"]
        collection = row["collection"]
        if collection == "patient":
            connection.execute(
                """
                INSERT OR IGNORE INTO patients (family_id, payload)
                VALUES (?, ?)
                """,
                (family_id, payload),
            )
        elif collection == "invites":
            invite = json.loads(payload)
            code = invite.get("code")
            if not isinstance(code, str) or not code.strip():
                raise ValueError("Não foi possível migrar convite sem código.")
            connection.execute(
                """
                INSERT OR IGNORE INTO invites
                    (family_id, invite_id, code, payload)
                VALUES (?, ?, ?, ?)
                """,
                (family_id, record_id, code.strip().upper(), payload),
            )
        else:
            target = {
                "medications": ("medications", "medication_id"),
                "dose-records": ("dose_records", "record_id"),
                "inventory-movements": ("inventory_movements", "record_id"),
            }.get(collection)
            if target is None:
                raise ValueError(
                    f"Coleção SQLite legada não reconhecida: {collection}"
                )
            table, id_column = target
            connection.execute(
                f"""
                INSERT OR IGNORE INTO {table}
                    (family_id, {id_column}, payload)
                VALUES (?, ?, ?)
                """,
                (family_id, record_id, payload),
            )


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone() is not None


class DomainError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
