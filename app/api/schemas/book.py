from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.book import BookStatus


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    genre: str | None = None


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    isbn: str | None = None
    publisher: str | None = None
    publication_year: int | None = None
    genre: str | None = None


class BookStatusUpdate(BaseModel):
    status: BookStatus


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    author: str
    isbn: str | None
    publisher: str | None
    publication_year: int | None
    genre: str | None
    status: str
    created_at: datetime
    updated_at: datetime
