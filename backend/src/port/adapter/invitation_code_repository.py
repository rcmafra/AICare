from abc import ABC, abstractmethod
from typing import Any


class InvitationCodeRepository(ABC):
    @abstractmethod
    def list_invites(self, family_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def find_by_code(self, code: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def get_invite(
        self,
        family_id: str,
        invite_id: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def save_invite(
        self,
        family_id: str,
        invite: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def update_invite(
        self,
        family_id: str,
        invite_id: str,
        invite: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError
