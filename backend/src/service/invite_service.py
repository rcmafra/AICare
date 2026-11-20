from typing import Any
from datetime import datetime, timedelta, timezone
from secrets import choice
from uuid import uuid4

from database import DomainError
from port.adapter.invitation_code_repository import InvitationCodeRepository

VALID_INVITE_STATUSES = {
    "pendente",
    "pending",
    "revogado",
    "revoked",
    "accepted",
    "aceito",
    "utilizado",
    "used",
}


class InviteService:
    def __init__(self, repository: InvitationCodeRepository):
        self.repository = repository

    def list_invites(self, family_id: str) -> list[dict[str, Any]]:
        return self.repository.list_invites(family_id)

    def create_invite(
        self,
        family_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        code = ""
        for _ in range(10):
            candidate = "AIC-" + "".join(choice(alphabet) for _ in range(6))
            if not self.repository.find_by_code(candidate):
                code = candidate
                break
        if not code:
            raise DomainError(503, "Não foi possível gerar um código de convite.")

        now = datetime.now(timezone.utc)
        invite = {
            "id": f"invite-{uuid4().hex}",
            "code": code,
            "role": data["role"],
            "name": data.get("name", "").strip(),
            "createdAt": now.isoformat(),
            "expiresAt": (now + timedelta(days=7)).isoformat(),
            "status": "Pendente",
            "familyId": family_id,
        }
        return self.repository.save_invite(family_id, invite)

    def update_invite(
        self,
        family_id: str,
        invite_id: str,
        status: str,
    ) -> dict[str, Any]:
        invite = self.repository.get_invite(family_id, invite_id)
        if not invite:
            raise DomainError(404, "Convite não encontrado.")
        if status.strip().lower() not in VALID_INVITE_STATUSES:
            raise DomainError(400, "Status de convite inválido.")
        invite["status"] = status
        return self.repository.update_invite(
            family_id, invite_id, invite
        )
