from typing import Any
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from database import DomainError
from port.adapter.diary_repository import DiaryRepository


class DiaryService:
    def __init__(self, repository: DiaryRepository):
        self.repository = repository

    def list_records(self, family_id: str) -> list[dict[str, Any]]:
        return self.repository.list_records(family_id)

    def has_photo(self, family_id: str, record_date: str) -> bool:
        return self.repository.has_photo(family_id, record_date)

    def save_record(
        self,
        family_id: str,
        record: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            local_timezone = ZoneInfo(record.pop("timezone", "UTC"))
        except ZoneInfoNotFoundError as error:
            raise DomainError(400, "Fuso horário inválido.") from error

        try:
            record_date = datetime.strptime(record["date"], "%Y-%m-%d").date()
        except ValueError as error:
            raise DomainError(400, "Data do Diário inválida.") from error

        existing = self.repository.get_record(family_id, record["date"])
        today = datetime.now(local_timezone).date()
        if not existing and record_date != today:
            raise DomainError(
                400, "Novas publicações só podem ser criadas para a data atual."
            )
        image_data = record.get("imageData")
        previous_image = existing.get("imageData") if existing else None
        if previous_image and image_data and image_data != previous_image:
            raise DomainError(
                400, "A foto de uma publicação existente não pode ser substituída."
            )
        if image_data and not previous_image and record_date != today:
            raise DomainError(400, "Fotos só podem ser publicadas na data atual.")
        if not record.get("observation", "").strip() and not image_data:
            raise DomainError(
                400, "Adicione um comentário ou uma foto antes de publicar."
            )

        now = datetime.now(timezone.utc).isoformat()
        record["createdAt"] = existing["createdAt"] if existing else now
        record["updatedAt"] = now if existing else None
        return self.repository.save_record(family_id, record)

    def delete_record(self, family_id: str, record_date: str) -> None:
        self.repository.delete_record(family_id, record_date)
