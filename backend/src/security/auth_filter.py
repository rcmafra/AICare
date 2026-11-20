from fastapi import Header

from service.auth_service import AuthService


def create_family_access_dependency(service: AuthService):
    def require_family_access(
            family_id: str,
            authorization: str | None = Header(default=None),
    ) -> None:
        service.require_family_access(family_id, authorization)

    return require_family_access
