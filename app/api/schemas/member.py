from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.member import MemberStatus


class MemberCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    address: str | None = None


class MemberUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None


class MemberStatusUpdate(BaseModel):
    status: MemberStatus


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    phone: str | None
    address: str | None
    status: str
    created_at: datetime
    updated_at: datetime
