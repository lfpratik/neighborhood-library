from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models import Base

if TYPE_CHECKING:
    from app.database.models.book import Book
    from app.database.models.member import Member


class Borrow(Base):
    __tablename__ = "borrows"

    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id"), nullable=False, index=True)
    member_id: Mapped[UUID] = mapped_column(ForeignKey("members.id"), nullable=False, index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    book: Mapped["Book"] = relationship("Book", back_populates="borrows")
    member: Mapped["Member"] = relationship("Member", back_populates="borrows")

    __table_args__ = (
        Index("ix_borrows_book_active", "book_id", "returned_at"),
        Index("ix_borrows_member_active", "member_id", "returned_at"),
        Index("ix_borrows_due_date", "due_date"),
        # Prevents concurrent duplicate active borrows for the same book at the DB level.
        # Application-level check in borrow_service is a fast path; this is the safety net.
        Index(
            "uq_borrows_one_active_per_book",
            "book_id",
            unique=True,
            postgresql_where=text("returned_at IS NULL"),
        ),
    )
