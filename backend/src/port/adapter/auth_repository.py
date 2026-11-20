from abc import ABC, abstractmethod
from typing import Any


class AuthRepository(ABC):
    @abstractmethod
    def create_user(
        self,
        user: dict[str, Any],
        password_hash: str,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def add_member_from_invite(
        self,
        user: dict[str, Any],
        password_hash: str,
        invite: dict[str, Any],
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def create_session(self, user_id: str, expires_at: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_user_by_token(self, token: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def delete_session(self, token: str) -> None:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def hash_password(password: str) -> str:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def verify_password(password: str, encoded_hash: str) -> bool:
        raise NotImplementedError
