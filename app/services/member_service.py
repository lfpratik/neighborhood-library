from uuid import UUID

from app.api.schemas.member import MemberCreate, MemberStatusUpdate, MemberUpdate
from app.database.models.member import Member
from app.database.repositories.member_repository import MemberRepository
from app.domain.member import (
    MemberNotFoundError,
    MemberStatus,
    validate_member_status_transition,
)


class MemberService:
    def __init__(self, repo: MemberRepository) -> None:
        self.repo = repo

    def create_member(self, data: MemberCreate) -> Member:
        """Register a new member. Rejects duplicate emails."""
        if self.repo.get_by_email(data.email) is not None:
            raise ValueError(f"Email '{data.email}' is already registered")
        member = self.repo.create(data.model_dump())
        self.repo.db.commit()
        self.repo.db.refresh(member)
        return member

    def get_member(self, member_id: UUID) -> Member:
        """Fetch a member by ID or raise MemberNotFoundError."""
        member = self.repo.get_by_id(member_id)
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
        return self.repo.get_all(page=page, size=size, status=status, search=search)

    def update_member(self, member_id: UUID, data: MemberUpdate) -> Member:
        """Update mutable member fields."""
        self.get_member(member_id)
        updates = data.model_dump(exclude_unset=True)
        member = self.repo.update(member_id, updates)
        self.repo.db.commit()
        self.repo.db.refresh(member)
        return member

    def update_status(self, member_id: UUID, data: MemberStatusUpdate) -> Member:
        """Change member status. Domain layer validates the transition."""
        member = self.get_member(member_id)
        validate_member_status_transition(MemberStatus(member.status), data.status)
        member = self.repo.update_status(member_id, data.status.value)
        self.repo.db.commit()
        self.repo.db.refresh(member)
        return member
