from typing import Any

from fastapi import APIRouter, Depends, status

from dto.schemas import InviteCreateInput
from security.auth_filter import create_family_access_dependency
from service.auth_service import AuthService
from service.invite_service import InviteService


def create_invite_router(
        service: InviteService,
        auth_service: AuthService,
) -> APIRouter:
    router = APIRouter(tags=["invites"])
    require_family_access = create_family_access_dependency(auth_service)

    @router.get("/families/{family_id}/invites")
    def list_invites(
            family_id: str,
            _: None = Depends(require_family_access),
    ) -> list[dict[str, Any]]:
        return service.list_invites(family_id)

    @router.post(
        "/families/{family_id}/invites",
        status_code=status.HTTP_201_CREATED,
    )
    def create_invite(
            family_id: str,
            data: InviteCreateInput,
            _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.create_invite(family_id, data.model_dump())

    @router.patch("/families/{family_id}/invites/{invite_id}")
    def update_invite(
            family_id: str,
            invite_id: str,
            status: str,
            _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.update_invite(family_id, invite_id, status)

    return router
