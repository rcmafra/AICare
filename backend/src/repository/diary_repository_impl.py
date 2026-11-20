import json
from typing import Any

from database import get_connection
from port.adapter.diary_repository import DiaryRepository


class DiaryRepositoryImpl(DiaryRepository):
    def get_record(
        self,
        family_id: str,
        record_date: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT payload FROM diary_records
                WHERE family_id = ? AND record_date = ?
                """,
                (family_id, record_date),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_records(self, family_id: str) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM diary_records
                WHERE family_id = ?
                ORDER BY record_date
                """,
                (family_id,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def has_photo(self, family_id: str, record_date: str) -> bool:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT payload FROM diary_records
                WHERE family_id = ? AND record_date = ?
                """,
                (family_id, record_date),
            ).fetchone()
        return bool(row and json.loads(row["payload"]).get("imageData"))

    def save_record(
        self,
        family_id: str,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO diary_records (family_id, record_date, payload)
                VALUES (?, ?, ?)
                ON CONFLICT (family_id, record_date)
                DO UPDATE SET payload = excluded.payload
                """,
                (
                    family_id,
                    record["date"],
                    json.dumps(record, ensure_ascii=False),
                ),
            )
        return record

    def delete_record(self, family_id: str, record_date: str) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM diary_records
                WHERE family_id = ? AND record_date = ?
                """,
                (family_id, record_date),
            )
