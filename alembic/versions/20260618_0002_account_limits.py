"""demo flag, subscription, analyses counter

Revision ID: 0003_account_limits
Revises: 0002_telegram_link
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_account_limits"
down_revision: str | None = "0002_telegram_link"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column(
            "is_subscribed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "users",
        sa.Column("analyses_used", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "analyses_used")
    op.drop_column("users", "is_subscribed")
    op.drop_column("users", "is_demo")
