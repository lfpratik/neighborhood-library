from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.logging import log_db_call
from app.database.models.borrow import Borrow
from app.database.repositories import BaseRepository


class BorrowRepository(BaseRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, borrow_id: UUID) -> Borrow | None:
        stmt = (
            select(Borrow)
            .where(Borrow.id == borrow_id)
            .options(joinedload(Borrow.book), joinedload(Borrow.member))
        )
        return self.db.scalar(stmt)

    def get_all(
        self,
        page: int,
        size: int,
        member_id: UUID | None = None,
        book_id: UUID | None = None,
        active: bool | None = None,
        overdue: bool | None = None,
    ) -> tuple[list[Borrow], int]:
        stmt = select(Borrow).options(joinedload(Borrow.book), joinedload(Borrow.member))
        if member_id is not None:
            stmt = stmt.where(Borrow.member_id == member_id)
        if book_id is not None:
            stmt = stmt.where(Borrow.book_id == book_id)
        if active is True:
            stmt = stmt.where(Borrow.returned_at.is_(None))
        elif active is False:
            stmt = stmt.where(Borrow.returned_at.is_not(None))
        if overdue is True:
            now = datetime.now(UTC)
            stmt = stmt.where(Borrow.due_date < now, Borrow.returned_at.is_(None))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt)
        items = (
            self.db.scalars(
                stmt.order_by(Borrow.borrowed_at.desc()).offset((page - 1) * size).limit(size)
            )
            .unique()
            .all()
        )
        return list(items), total or 0

    def get_active_by_book_id(self, book_id: UUID) -> Borrow | None:
        stmt = select(Borrow).where(Borrow.book_id == book_id, Borrow.returned_at.is_(None))
        return self.db.scalar(stmt)

    @log_db_call("db_create_borrow")
    def create(self, data: dict) -> Borrow:
        borrow = Borrow(**data)
        self.db.add(borrow)
        self.db.flush()
        return borrow

    @log_db_call("db_update_borrow_returned_at")
    def update_returned_at(self, borrow_id: UUID, returned_at: datetime) -> Borrow:
        borrow = cast(Borrow, self.db.get(Borrow, borrow_id))
        borrow.returned_at = returned_at
        self.db.flush()
        return borrow
