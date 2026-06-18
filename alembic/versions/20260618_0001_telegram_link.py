"""telegram username + link token

Revision ID: 0002_telegram_link
Revises: 0001_initial
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_telegram_link"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_username", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("tg_link_token", sa.String(32), nullable=True))
    op.create_index("ix_users_tg_link_token", "users", ["tg_link_token"])


def downgrade() -> None:
    op.drop_index("ix_users_tg_link_token", table_name="users")
    op.drop_column("users", "tg_link_token")
    op.drop_column("users", "telegram_username")
