import json
import sqlite3
from typing import Any, Callable

from database import get_connection
from port.adapter.medication_repository import MedicationRepository


class MedicationRepositoryImpl(MedicationRepository):
    def list_medications(self, family_id: str) -> list[dict[str, Any]]:
        return self._list_records(family_id, "medications")

    def save_medication(
        self,
        family_id: str,
        medication_id: str,
        medication: dict[str, Any],
    ) -> dict[str, Any]:
        with get_connection() as connection:
            self._upsert_record(
                connection,
                "medications",
                "medication_id",
                family_id,
                medication_id,
                medication,
            )
        return medication

    def delete_medication(
        self,
        family_id: str,
        medication_id: str,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                DELETE FROM medications
                WHERE family_id = ? AND medication_id = ?
                """,
                (family_id, medication_id),
            )

    def get_medication_state(self, family_id: str) -> dict[str, Any]:
        return {
            "doseRecords": self._list_records(family_id, "dose_records"),
            "inventoryMovements": self._list_records(
                family_id, "inventory_movements"
            ),
        }

    def transact_medication_data(
        self,
        family_id: str,
        operation: Callable[
            [list[dict[str, Any]], dict[str, list[dict[str, Any]]]],
            tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], Any],
        ],
    ) -> Any:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            medicines = self._list_records_from_connection(
                connection, family_id, "medications"
            )
            state = {
                "doseRecords": self._list_records_from_connection(
                    connection, family_id, "dose_records"
                ),
                "inventoryMovements": self._list_records_from_connection(
                    connection, family_id, "inventory_movements"
                ),
            }
            updated_medicines, updated_state, result = operation(
                medicines, state
            )

            for table, records, id_column in (
                ("medications", updated_medicines, "medication_id"),
                ("dose_records", updated_state["doseRecords"], "record_id"),
                (
                    "inventory_movements",
                    updated_state["inventoryMovements"],
                    "record_id",
                ),
            ):
                connection.execute(
                    f"DELETE FROM {table} WHERE family_id = ?",
                    (family_id,),
                )
                for record in records:
                    record_id = str(record.get("id") or "")
                    if not record_id:
                        continue
                    self._upsert_record(
                        connection,
                        table,
                        id_column,
                        family_id,
                        record_id,
                        record,
                    )

            return result

    @staticmethod
    def _list_records(
        family_id: str,
        table: str,
    ) -> list[dict[str, Any]]:
        with get_connection() as connection:
            return MedicationRepositoryImpl._list_records_from_connection(
                connection, family_id, table
            )

    @staticmethod
    def _list_records_from_connection(
        connection: sqlite3.Connection,
        family_id: str,
        table: str,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            f"""
            SELECT payload FROM {table}
            WHERE family_id = ?
            ORDER BY rowid
            """,
            (family_id,),
        ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    @staticmethod
    def _upsert_record(
        connection: sqlite3.Connection,
        table: str,
        id_column: str,
        family_id: str,
        record_id: str,
        payload: dict[str, Any],
    ) -> None:
        connection.execute(
            f"""
            INSERT INTO {table} (family_id, {id_column}, payload)
            VALUES (?, ?, ?)
            ON CONFLICT (family_id, {id_column})
            DO UPDATE SET payload = excluded.payload
            """,
            (
                family_id,
                record_id,
                json.dumps(payload, ensure_ascii=False),
            ),
        )
