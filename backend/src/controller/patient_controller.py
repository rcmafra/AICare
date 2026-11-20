from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from dto.schemas import PatientInput
from security.auth_filter import create_family_access_dependency
from service.auth_service import AuthService
from service.patient_service import PatientService


def create_patient_router(
        service: PatientService,
        auth_service: AuthService,
) -> APIRouter:
    router = APIRouter(tags=["patients"])
    require_family_access = create_family_access_dependency(auth_service)

    @router.get("/families/{family_id}/patient")
    def get_patient(
            family_id: str,
            _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        patient = service.get_patient(family_id)
        if patient is None:
            raise HTTPException(status_code=404, detail="Paciente não encontrado.")
        return patient

    @router.put("/families/{family_id}/patient")
    def save_patient(
            family_id: str,
            data: PatientInput,
            _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.save_patient(family_id, data.model_dump())

    @router.delete(
        "/families/{family_id}/patient",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def delete_patient(
            family_id: str,
            _: None = Depends(require_family_access),
    ) -> Response:
        service.delete_patient(family_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
