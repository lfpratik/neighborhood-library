import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.domain.member import MemberStatus

_PHONE_RE = re.compile(r"^\+?[\d\s\-().]{7,20}$")


def _validate_phone(v: str | None) -> str | None:
    if v is not None and not _PHONE_RE.match(v):
        raise ValueError("Invalid phone number format")
    return v


class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None

    _check_phone = field_validator("phone")(_validate_phone)


class MemberUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None

    _check_phone = field_validator("phone")(_validate_phone)


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
