from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models import Base
from app.domain.book import BookStatus

if TYPE_CHECKING:
    from app.database.models.borrow import Borrow


class Book(Base):
    __tablename__ = "books"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(13), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=BookStatus.AVAILABLE.value
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    borrows: Mapped[list["Borrow"]] = relationship("Borrow", back_populates="book")

    __table_args__ = (
        Index("ix_books_status", "status"),
        UniqueConstraint("isbn", name="uq_books_isbn"),
    )
