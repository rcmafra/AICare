from typing import Any
from datetime import datetime, timezone
from uuid import uuid4

from database import DomainError
from port.adapter.patient_repository import PatientRepository


class PatientService:
    def __init__(self, repository: PatientRepository):
        self.repository = repository

    def get_patient(self, family_id: str) -> dict[str, Any] | None:
        return self.repository.get_patient(family_id)

    def save_patient(
        self,
        family_id: str,
        patient: dict[str, Any],
    ) -> dict[str, Any]:
        name = patient.get("name", "").strip()
        if not name:
            raise DomainError(400, "Informe o nome do paciente.")
        previous = self.repository.get_patient(family_id)
        now = datetime.now(timezone.utc).isoformat()
        stored_patient = {
            "id": previous["id"] if previous else f"patient-{uuid4().hex}",
            "familyId": family_id,
            "name": name,
            "birthDate": patient.get("birthDate", "").strip(),
            "relationship": patient.get("relationship", "").strip(),
            "notes": patient.get("notes", "").strip(),
            "createdAt": previous["createdAt"] if previous else now,
            "updatedAt": now,
        }
        return self.repository.save_patient(family_id, stored_patient)

    def delete_patient(self, family_id: str) -> None:
        self.repository.delete_patient(family_id)
