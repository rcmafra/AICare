from abc import ABC, abstractmethod
from typing import Any, Callable


class MedicationRepository(ABC):
    @abstractmethod
    def list_medications(self, family_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def save_medication(
        self,
        family_id: str,
        medication_id: str,
        medication: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def delete_medication(
        self,
        family_id: str,
        medication_id: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_medication_state(self, family_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def transact_medication_data(
        self,
        family_id: str,
        operation: Callable[
            [list[dict[str, Any]], dict[str, list[dict[str, Any]]]],
            tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], Any],
        ],
    ) -> Any:
        raise NotImplementedError
