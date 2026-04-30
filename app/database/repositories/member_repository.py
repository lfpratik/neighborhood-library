from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.logging import log_db_call
from app.database.models.member import Member
from app.database.repositories import BaseRepository


class MemberRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, member_id: UUID) -> Member | None:
        return self.db.get(Member, member_id)

    def get_by_email(self, email: str) -> Member | None:
        return self.db.scalar(select(Member).where(Member.email == email))

    def get_all(
        self,
        page: int,
        size: int,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Member], int]:
        stmt = select(Member)
        if status is not None:
            stmt = stmt.where(Member.status == status)
        if search is not None:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Member.name.ilike(pattern), Member.email.ilike(pattern)))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = self.db.scalars(
            stmt.order_by(Member.name).offset((page - 1) * size).limit(size)
        ).all()
        return list(items), total or 0

    @log_db_call("db_create_member")
    def create(self, data: dict) -> Member:
        member = Member(**data)
        self.db.add(member)
        self.db.flush()
        return member

    @log_db_call("db_update_member")
    def update(self, member_id: UUID, data: dict) -> Member:
        member = cast(Member, self.db.get(Member, member_id))
        for key, value in data.items():
            setattr(member, key, value)
        self.db.flush()
        return member

    @log_db_call("db_update_member_status")
    def update_status(self, member_id: UUID, new_status: str) -> Member:
        member = cast(Member, self.db.get(Member, member_id))
        member.status = new_status
        self.db.flush()
        return member
