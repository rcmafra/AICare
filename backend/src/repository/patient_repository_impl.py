import json
from typing import Any

from database import get_connection
from port.adapter.patient_repository import PatientRepository


class PatientRepositoryImpl(PatientRepository):
    def get_patient(self, family_id: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT payload FROM patients WHERE family_id = ?
                """,
                (family_id,),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def save_patient(
        self,
        family_id: str,
        patient: dict[str, Any],
    ) -> dict[str, Any]:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO patients (family_id, payload)
                VALUES (?, ?)
                ON CONFLICT (family_id)
                DO UPDATE SET payload = excluded.payload
                """,
                (
                    family_id,
                    json.dumps(patient, ensure_ascii=False),
                ),
            )
        return patient

    def delete_patient(self, family_id: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM patients WHERE family_id = ?",
                (family_id,),
            )
