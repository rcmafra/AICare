from abc import ABC, abstractmethod
from typing import Any


class PatientRepository(ABC):
    @abstractmethod
    def get_patient(self, family_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def save_patient(
        self,
        family_id: str,
        patient: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete_patient(self, family_id: str) -> None:
        raise NotImplementedError
