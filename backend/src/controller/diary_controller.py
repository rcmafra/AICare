from typing import Any

from fastapi import APIRouter, Depends, Response, status

from dto.schemas import DiaryRecordInput
from security.auth_filter import create_family_access_dependency
from service.auth_service import AuthService
from service.diary_service import DiaryService


def create_diary_router(
    service: DiaryService,
    auth_service: AuthService,
) -> APIRouter:
    router = APIRouter(tags=["diary"])
    require_family_access = create_family_access_dependency(auth_service)

    @router.get("/families/{family_id}/diary")
    def list_records(
        family_id: str,
        _: None = Depends(require_family_access),
    ) -> list[dict[str, Any]]:
        return service.list_records(family_id)

    @router.get("/families/{family_id}/diary/{record_date}/photo")
    def has_photo(
        family_id: str,
        record_date: str,
        _: None = Depends(require_family_access),
    ) -> dict[str, bool]:
        return {"hasPhoto": service.has_photo(family_id, record_date)}

    @router.put("/families/{family_id}/diary/{record_date}")
    def save_record(
        family_id: str,
        record_date: str,
        data: DiaryRecordInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        record = data.model_dump()
        record["date"] = record_date
        return service.save_record(family_id, record)

    @router.delete(
        "/families/{family_id}/diary/{record_date}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_record(
        family_id: str,
        record_date: str,
        _: None = Depends(require_family_access),
    ) -> Response:
        service.delete_record(family_id, record_date)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
