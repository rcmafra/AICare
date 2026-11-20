import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controller.auth_controller import create_auth_router
from controller.diary_controller import create_diary_router
from controller.invite_controller import create_invite_router
from controller.medication_controller import create_medication_router
from controller.medication_assistant_controller import (
    create_medication_assistant_router,
)
from controller.patient_controller import create_patient_router
from database import DomainError, initialize_database
from repository.auth_repository_impl import AuthRepositoryImpl
from repository.diary_repository_impl import DiaryRepositoryImpl
from repository.invitation_code_repository_impl import (
    InvitationCodeRepositoryImpl,
)
from repository.medication_repository_impl import MedicationRepositoryImpl
from repository.patient_repository_impl import PatientRepositoryImpl
from service.auth_service import AuthService
from service.diary_service import DiaryService
from service.invite_service import InviteService
from service.medication_service import MedicationService
from service.medication_assistant_service import MedicationAssistantService
from service.patient_service import PatientService


initialize_database()
app = FastAPI(title="AICare API", version="1.0.0")
request_logger = logging.getLogger("aicare.requests")
request_logger.setLevel(logging.INFO)
request_logger.propagate = False
if not request_logger.handlers:
    request_handler = logging.StreamHandler()
    request_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    request_logger.addHandler(request_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    method = request.method
    path = request.url.path
    started_at = perf_counter()
    request_logger.info("Requisição recebida: %s %s", method, path)

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        request_logger.exception(
            "Falha ao processar requisição: %s %s status=500 duração_ms=%.2f",
            method,
            path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    request_logger.info(
        "Requisição processada: %s %s status=%d duração_ms=%.2f",
        method,
        path,
        response.status_code,
        duration_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

auth_repository = AuthRepositoryImpl()
invite_repository = InvitationCodeRepositoryImpl()
auth_service = AuthService(auth_repository, invite_repository)

app.include_router(create_auth_router(auth_service))
app.include_router(
    create_diary_router(DiaryService(DiaryRepositoryImpl()), auth_service)
)
app.include_router(
    create_patient_router(
        PatientService(PatientRepositoryImpl()),
        auth_service,
    )
)
app.include_router(
    create_invite_router(InviteService(invite_repository), auth_service)
)
app.include_router(
    create_medication_router(
        MedicationService(MedicationRepositoryImpl()),
        auth_service,
    )
)
app.include_router(
    create_medication_assistant_router(
        MedicationAssistantService(),
        auth_service,
    )
)


@app.exception_handler(DomainError)
async def handle_domain_error(
    request: Request,
    error: DomainError,
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
