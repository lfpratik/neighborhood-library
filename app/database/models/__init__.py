import uuid
from datetime import datetime
from uuid import UUID

import uuid_utils
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _new_uuid() -> UUID:
    return uuid.UUID(str(uuid_utils.uuid7()))


class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=_new_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Import models so Alembic autogenerate detects all tables
from app.database.models.book import Book  # noqa: E402, F401
from app.database.models.borrow import Borrow  # noqa: E402, F401
from app.database.models.member import Member  # noqa: E402, F401
