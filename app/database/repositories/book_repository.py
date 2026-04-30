from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.models.book import Book


class BookRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, book_id: UUID) -> Book | None:
        return self.db.get(Book, book_id)

    def get_all(
        self,
        page: int,
        size: int,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Book], int]:
        stmt = select(Book)
        if status is not None:
            stmt = stmt.where(Book.status == status)
        if search is not None:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Book.title.ilike(pattern), Book.author.ilike(pattern)))
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery()))
        items = self.db.scalars(
            stmt.order_by(Book.title).offset((page - 1) * size).limit(size)
        ).all()
        return list(items), total or 0

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.db.scalar(select(Book).where(Book.isbn == isbn))

    def create(self, data: dict) -> Book:
        book = Book(**data)
        self.db.add(book)
        self.db.flush()
        return book

    def update(self, book_id: UUID, data: dict) -> Book:
        book = cast(Book, self.db.get(Book, book_id))
        for key, value in data.items():
            setattr(book, key, value)
        self.db.flush()
        return book

    def update_status(self, book_id: UUID, new_status: str) -> Book:
        book = cast(Book, self.db.get(Book, book_id))
        book.status = new_status
        self.db.flush()
        return book
