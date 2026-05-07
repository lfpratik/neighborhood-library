"""add partial unique index for one active borrow per book

Revision ID: b3e8c1d2f4a5
Revises: a2031aeb0fcf
Create Date: 2026-04-30 22:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3e8c1d2f4a5"
down_revision: Union[str, None] = "a2031aeb0fcf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_borrows_one_active_per_book",
        "borrows",
        ["book_id"],
        unique=True,
        postgresql_where=sa.text("returned_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_borrows_one_active_per_book", table_name="borrows")
