import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from database import DomainError
from port.adapter.auth_repository import AuthRepository
from port.adapter.invitation_code_repository import InvitationCodeRepository


def _normalize_status(status: str) -> str:
    return status.strip().lower()


class AuthService:
    def __init__(
            self,
            repository: AuthRepository,
            invite_repository: InvitationCodeRepository,
    ):
        self.repository = repository
        self.invite_repository = invite_repository

    def register_user(self, data: dict[str, Any]) -> dict[str, Any]:
        email = data["email"].strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise DomainError(400, "Informe um e-mail válido.")
        if not data["name"].strip():
            raise DomainError(400, "Informe o nome.")
        if self.repository.get_user_by_email(email):
            raise DomainError(
                409, "Já existe uma conta cadastrada com esse e-mail."
            )

        invite_code = (data.get("inviteCode") or "").strip().upper()
        if invite_code:
            invite = self.invite_repository.find_by_code(invite_code)
            if not invite or not self._invite_is_available(invite):
                raise DomainError(400, "Código de convite inválido ou expirado.")
            family_id = str(invite["familyId"])
            role = invite["role"]
        else:
            invite = None
            family_id = f"family-{uuid4().hex}"
            role = "Administrador"

        user = {
            "id": data.get("id") or f"user-{uuid4().hex}",
            "name": data["name"].strip(),
            "email": email,
            "role": role,
            "familyId": family_id,
            "inviteCode": invite_code or None,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        password_hash = self.repository.hash_password(data["password"])

        try:
            if invite:
                invitation_accepted = self.repository.add_member_from_invite(
                    user, password_hash, invite
                )
                if not invitation_accepted:
                    raise DomainError(
                        400, "Código de convite inválido ou expirado."
                    )
            else:
                self.repository.create_user(user, password_hash)
        except sqlite3.IntegrityError as error:
            if self.repository.get_user_by_email(email):
                raise DomainError(
                    409, "Já existe uma conta cadastrada com esse e-mail."
                ) from error
            raise

        return self._create_session(user)

    def login(self, email: str, password: str) -> dict[str, Any]:
        row = self.repository.get_user_by_email(email.strip().lower())
        if not row or not self.repository.verify_password(
                password, row["password_hash"]
        ):
            raise DomainError(401, "E-mail ou senha incorretos.")

        return self._create_session(
            {
                "id": row["id"],
                "name": row["name"],
                "email": row["email"],
                "role": row["role"],
                "familyId": row["family_id"],
                "inviteCode": row["invite_code"],
            }
        )

    def authenticate(self, authorization: str | None) -> dict[str, Any]:
        if not authorization or not authorization.startswith("Bearer "):
            raise DomainError(401, "Autenticação necessária.")
        token = authorization.removeprefix("Bearer ").strip()
        user = self.repository.get_user_by_token(token)
        if not user:
            raise DomainError(401, "Sessão inválida ou expirada.")
        return {
            "id": user["id"],
            "familyId": user["family_id"],
            "role": user["role"],
        }

    def get_session_user(
        self,
        authorization: str | None,
    ) -> dict[str, Any]:
        authenticated = self.authenticate(authorization)
        token = authorization.removeprefix("Bearer ").strip()
        user = self.repository.get_user_by_token(token)
        if not user:
            raise DomainError(401, "Sessão inválida ou expirada.")
        return self._public_user(
            {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "familyId": authenticated["familyId"],
                "inviteCode": user["invite_code"],
            }
        )

    def require_family_access(
            self,
            family_id: str,
            authorization: str | None,
    ) -> None:
        user = self.authenticate(authorization)
        if user["familyId"] != family_id:
            raise DomainError(403, "Acesso não autorizado a esta família.")

    def require_family_admin_access(
            self,
            family_id: str,
            authorization: str | None,
    ) -> None:
        user = self.authenticate(authorization)
        if user["familyId"] != family_id:
            raise DomainError(403, "Acesso não autorizado a esta família.")
        if user["role"] != "Administrador":
            raise DomainError(
                403,
                "Somente membros administradores podem gerar convites.",
            )

    def logout(self, authorization: str | None) -> None:
        self.authenticate(authorization)
        token = authorization.removeprefix("Bearer ").strip()
        self.repository.delete_session(token)

    def _create_session(self, user: dict[str, Any]) -> dict[str, Any]:
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        token = self.repository.create_session(
            user["id"], expires_at.isoformat()
        )
        return {
            "user": self._public_user(user),
            "accessToken": token,
        }

    @staticmethod
    def _invite_is_available(invite: dict[str, Any]) -> bool:
        status = _normalize_status(invite["status"])
        if status not in {"pendente", "pending"}:
            return False
        try:
            expires_at = datetime.fromisoformat(
                invite["expiresAt"].replace("Z", "+00:00")
            )
        except (KeyError, TypeError, ValueError):
            return False
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)

    @staticmethod
    def _public_user(user: dict[str, Any]) -> dict[str, Any]:
        return {
            key: user[key]
            for key in ("id", "name", "email", "role", "familyId", "inviteCode")
            if key in user
        }
