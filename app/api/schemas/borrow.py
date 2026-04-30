from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from app.api.schemas.book import BookResponse
from app.api.schemas.member import MemberResponse


class BorrowCreate(BaseModel):
    book_id: UUID
    member_id: UUID
    notes: str | None = None


class BorrowSummaryResponse(BaseModel):
    """Flat borrow representation for list endpoints.

    Includes denormalized book_title and member_name so callers have display
    names without receiving full nested objects.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    member_id: UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    notes: str | None
    created_at: datetime
    book_title: str
    member_name: str

    @model_validator(mode="before")
    @classmethod
    def _extract_display_names(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "book_id": data.book_id,
            "member_id": data.member_id,
            "borrowed_at": data.borrowed_at,
            "due_date": data.due_date,
            "returned_at": data.returned_at,
            "notes": data.notes,
            "created_at": data.created_at,
            "book_title": data.book.title,
            "member_name": data.member.name,
        }


class BorrowResponse(BaseModel):
    """Full borrow representation for detail/create/return endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    member_id: UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    notes: str | None
    created_at: datetime
    book: BookResponse
    member: MemberResponse
