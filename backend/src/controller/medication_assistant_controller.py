from typing import Any

from fastapi import APIRouter, Depends

from dto.schemas import MedicationAssistantAnswerInput
from security.auth_filter import create_family_access_dependency
from service.auth_service import AuthService
from service.medication_assistant_service import MedicationAssistantService


def create_medication_assistant_router(
    service: MedicationAssistantService,
    auth_service: AuthService,
) -> APIRouter:
    router = APIRouter(tags=["medication assistant"])
    require_family_access = create_family_access_dependency(auth_service)

    @router.post(
        "/families/{family_id}/medication-assistant/answer"
    )
    def process_answer(
        family_id: str,
        data: MedicationAssistantAnswerInput,
        _: None = Depends(require_family_access),
    ) -> dict[str, Any]:
        return service.process_answer(
            data.step, data.answer, data.draft
        )

    return router
