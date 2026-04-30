from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.api.schemas.member import MemberCreate, MemberStatusUpdate, MemberUpdate
from app.database.models.member import Member
from app.domain.member import (
    DuplicateEmailError,
    MemberNotFoundError,
    MemberStatus,
    validate_member_status_transition,
)

if TYPE_CHECKING:
    from app.database.unit_of_work import UnitOfWork


class MemberService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create_member(self, data: MemberCreate) -> Member:
        """Register a new member."""
        try:
            return self.uow.members.create(data.model_dump())
        except IntegrityError as ie:
            email = data.email
            msg = f"Email '{email}' is already registered" if email else "Email already registered"
            raise DuplicateEmailError(msg) from ie

    def get_member(self, member_id: UUID) -> Member:
        """Fetch a member by ID or raise MemberNotFoundError."""
        member = self.uow.members.get_by_id(member_id)
        if member is None:
            raise MemberNotFoundError(f"Member {member_id} not found")
        return member

    def list_members(
        self,
        page: int,
        size: int,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Member], int]:
        """List members with optional status and search filters."""
        return self.uow.members.get_all(page=page, size=size, status=status, search=search)

    def replace_member(self, member_id: UUID, data: MemberUpdate) -> Member:
        """Full replacement — all fields written, unset fields cleared to None (PUT)."""
        self.get_member(member_id)
        payload = data.model_dump(exclude_unset=False)  # ✅ true PUT
        try:
            return self.uow.members.update(member_id, payload)
        except IntegrityError as ie:
            email = data.email
            msg = f"Email '{email}' is already registered" if email else "Email already registered"
            raise DuplicateEmailError(msg) from ie

    def update_member(self, member_id: UUID, data: MemberUpdate) -> Member:
        """Partial update — only provided fields written, others left unchanged (PATCH)."""
        self.get_member(member_id)
        updates = data.model_dump(exclude_unset=True)
        try:
            return self.uow.members.update(member_id, updates)
        except IntegrityError as ie:
            email = updates.get("email")
            msg = f"Email '{email}' is already registered" if email else "Email already registered"
            raise DuplicateEmailError(msg) from ie

    def update_status(self, member_id: UUID, data: MemberStatusUpdate) -> Member:
        """Change member status. Domain layer validates the transition."""
        member = self.get_member(member_id)
        validate_member_status_transition(MemberStatus(member.status), data.status)
        return self.uow.members.update_status(member_id, data.status.value)
