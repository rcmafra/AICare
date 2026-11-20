from typing import Any


class DiaryRepository:
    def get_record(
        self,
        family_id: str,
        record_date: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    def list_records(self, family_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def has_photo(self, family_id: str, record_date: str) -> bool:
        raise NotImplementedError

    def save_record(
        self,
        family_id: str,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    def delete_record(self, family_id: str, record_date: str) -> None:
        raise NotImplementedError
