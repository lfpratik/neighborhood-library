from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models import Base
from app.domain.member import MemberStatus

if TYPE_CHECKING:
    from app.database.models.borrow import Borrow


class Member(Base):
    __tablename__ = "members"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=MemberStatus.ACTIVE.value
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    borrows: Mapped[list["Borrow"]] = relationship("Borrow", back_populates="member")

    __table_args__ = (UniqueConstraint("email", name="uq_members_email"),)
