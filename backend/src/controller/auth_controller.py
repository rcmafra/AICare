from typing import Any

from fastapi import APIRouter, Header, Response, status

from dto.schemas import UserCredentials, UserRegister
from service.auth_service import AuthService


def create_auth_router(service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/register", status_code=status.HTTP_201_CREATED)
    def register(data: UserRegister) -> dict[str, Any]:
        return service.register_user(data.model_dump())

    @router.post("/login")
    def login(data: UserCredentials) -> dict[str, Any]:
        return service.login(data.email, data.password)

    @router.get("/session")
    def get_session(
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        return {"user": service.get_session_user(authorization)}

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(
        authorization: str | None = Header(default=None),
    ) -> Response:
        service.logout(authorization)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
