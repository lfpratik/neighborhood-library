from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.api.schemas.book import BookResponse
from app.api.schemas.member import MemberResponse


class BorrowCreate(BaseModel):
    book_id: UUID
    member_id: UUID
    notes: str | None = None


class BorrowResponse(BaseModel):
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
