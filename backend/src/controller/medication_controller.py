from typing import Any

from fastapi import APIRouter, Depends, Response, status

from dto.schemas import (
    DoseActionInput,
    DoseUndoInput,
    MedicationInput,
    StockReplenishmentInput,
)
from security.auth_filter import create_family_access_dependency
from service.auth_service import AuthService
from service.medication_service import MedicationService


def create_medication_router(
    service: MedicationService,
    auth_service: AuthService,
) -> APIRouter:
    router = APIRouter(tags=["medications"])
    require_family_access = create_family_access_dependency(auth_service)

    @router.get("/families/{family_id}/medications")
    def list_medications(
        family_id: str,
        _: None = Depends(require_family_access),
    ) -> list[dict[str, Any]]:
        return service.list_medications(family_id)

    @router.post(
        "/families/{family_id}/medications",
        status_code=status.HTTP_201_CREATED,
    )
    def create_medication(
        family_id: str,
        data: MedicationInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.save_medication(
            family_id, data.id, data.model_dump(exclude_none=True)
        )

    @router.put("/families/{family_id}/medications/{medication_id}")
    def update_medication(
        family_id: str,
        medication_id: str,
        data: MedicationInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.save_medication(
            family_id, medication_id, data.model_dump(exclude_none=True)
        )

    @router.delete(
        "/families/{family_id}/medications/{medication_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_medication(
        family_id: str,
        medication_id: str,
        _: None = Depends(require_family_access),
    ) -> Response:
        service.delete_medication(family_id, medication_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post(
        "/families/{family_id}/medications/{medication_id}/toggle"
    )
    def toggle_medication(
        family_id: str,
        medication_id: str,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.toggle_medication(family_id, medication_id)

    @router.get("/families/{family_id}/medication-state")
    def get_medication_state(
        family_id: str,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.get_medication_state(family_id)

    @router.get("/families/{family_id}/medication-schedule")
    def get_medication_schedule(
        family_id: str,
        date: str,
        timezone: str,
        _: None = Depends(require_family_access),
    ) -> list[dict[str, Any]]:
        return service.get_schedule(family_id, date, timezone)

    @router.post("/families/{family_id}/medication-doses/administer")
    def administer_dose(
        family_id: str,
        data: DoseActionInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, str]:
        return service.administer_dose(
            family_id, data.doseId, data.date, data.timezone
        )

    @router.post("/families/{family_id}/medication-doses/undo")
    def undo_dose(
        family_id: str,
        data: DoseUndoInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, str]:
        return service.undo_dose(family_id, data.doseId)

    @router.post(
        "/families/{family_id}/medications/{medication_id}/replenishments"
    )
    def replenish_stock(
        family_id: str,
        medication_id: str,
        data: StockReplenishmentInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.replenish_stock(
            family_id, medication_id, data.quantity, data.description
        )

    return router
