import hashlib
import hmac
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Any

from database import get_connection
from port.adapter.auth_repository import AuthRepository


class AuthRepositoryImpl(AuthRepository):
    def create_user(
        self,
        user: dict[str, Any],
        password_hash: str,
    ) -> dict[str, Any]:
        with get_connection() as connection:
            self._insert_user(connection, user, password_hash)
        return user

    def add_member_from_invite(
        self,
        user: dict[str, Any],
        password_hash: str,
        invite: dict[str, Any],
    ) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT payload FROM invites
                WHERE family_id = ? AND invite_id = ?
                """,
                (user["familyId"], invite["id"]),
            ).fetchone()
            if not row:
                return False

            current_invite = json.loads(row["payload"])
            if not self._invite_is_available(current_invite):
                return False
            if (
                current_invite.get("code", "").strip().upper()
                != invite.get("code", "").strip().upper()
            ):
                return False

            self._insert_user(connection, user, password_hash)
            current_invite["status"] = "accepted"
            connection.execute(
                """
                UPDATE invites SET payload = ?
                WHERE family_id = ? AND invite_id = ?
                """,
                (
                    json.dumps(current_invite, ensure_ascii=False),
                    user["familyId"],
                    current_invite["id"],
                ),
            )
        return True

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM family_members WHERE email = ? COLLATE NOCASE",
                (email,),
            ).fetchone()
        return dict(row) if row else None

    def create_session(self, user_id: str, expires_at: str) -> str:
        token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO sessions (token_hash, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (token_hash, user_id, expires_at),
            )
        return token

    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT family_members.* FROM sessions
                JOIN family_members ON family_members.id = sessions.user_id
                WHERE sessions.token_hash = ? AND sessions.expires_at > ?
                """,
                (token_hash, datetime.now(timezone.utc).isoformat()),
            ).fetchone()
        return dict(row) if row else None

    def delete_session(self, token: str) -> None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?",
                (token_hash,),
            )

    @staticmethod
    def hash_password(password: str, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, 310_000
        )
        return f"{salt.hex()}:{digest.hex()}"

    @staticmethod
    def verify_password(password: str, encoded_hash: str) -> bool:
        try:
            salt_hex, expected = encoded_hash.split(":", maxsplit=1)
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt_hex), 310_000
            ).hex()
        except ValueError:
            return False
        return hmac.compare_digest(actual, expected)

    @staticmethod
    def _invite_is_available(invite: dict[str, Any]) -> bool:
        if invite.get("status", "").strip().lower() not in {
            "pendente",
            "pending",
        }:
            return False
        try:
            expires_at = datetime.fromisoformat(
                invite["expiresAt"].replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError):
            return False
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)

    @staticmethod
    def _insert_user(
        connection: sqlite3.Connection,
        user: dict[str, Any],
        password_hash: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO family_members
                (id, family_id, name, email, password_hash, role,
                 invite_code, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"],
                user["familyId"],
                user["name"],
                user["email"],
                password_hash,
                user["role"],
                user.get("inviteCode"),
                user["createdAt"],
            ),
        )
