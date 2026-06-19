"""widen wb_token_encrypted to TEXT

Revision ID: 0004_widen_wb_token
Revises: 0003_account_limits
Create Date: 2026-06-19

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_widen_wb_token"
down_revision: str | None = "0003_account_limits"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "wb_token_encrypted",
        type_=sa.Text(),
        existing_type=sa.String(512),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "wb_token_encrypted",
        type_=sa.String(512),
        existing_type=sa.Text(),
        existing_nullable=True,
    )
