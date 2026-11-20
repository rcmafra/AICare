import json
from typing import Any

from database import get_connection
from port.adapter.invitation_code_repository import InvitationCodeRepository


class InvitationCodeRepositoryImpl(InvitationCodeRepository):
    def list_invites(self, family_id: str) -> list[dict[str, Any]]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT payload FROM invites
                WHERE family_id = ?
                ORDER BY rowid
                """,
                (family_id,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def find_by_code(self, code: str) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT family_id, payload FROM invites
                WHERE code = ? COLLATE NOCASE
                """,
                (code,),
            ).fetchone()
        if not row:
            return None
        invite = json.loads(row["payload"])
        invite["familyId"] = row["family_id"]
        return invite

    def get_invite(
        self,
        family_id: str,
        invite_id: str,
    ) -> dict[str, Any] | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT payload FROM invites
                WHERE family_id = ? AND invite_id = ?
                """,
                (family_id, invite_id),
            ).fetchone()
        return json.loads(row["payload"]) if row else None

    def save_invite(
        self,
        family_id: str,
        invite: dict[str, Any],
    ) -> dict[str, Any]:
        return self._upsert_invite(family_id, invite["id"], invite)

    def update_invite(
        self,
        family_id: str,
        invite_id: str,
        invite: dict[str, Any],
    ) -> dict[str, Any]:
        return self._upsert_invite(family_id, invite_id, invite)

    @staticmethod
    def _upsert_invite(
        family_id: str,
        invite_id: str,
        invite: dict[str, Any],
    ) -> dict[str, Any]:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO invites (family_id, invite_id, code, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (family_id, invite_id)
                DO UPDATE SET code = excluded.code, payload = excluded.payload
                """,
                (
                    family_id,
                    invite_id,
                    invite["code"].strip().upper(),
                    json.dumps(invite, ensure_ascii=False),
                ),
            )
        return invite
