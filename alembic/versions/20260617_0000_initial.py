"""initial schema: users, sales, orders, stocks

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("wb_token_encrypted", sa.String(512), nullable=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("srid", sa.String(128), nullable=False),
        sa.Column("sale_id", sa.String(64), nullable=True),
        sa.Column("nm_id", sa.BigInteger(), nullable=True),
        sa.Column("supplier_article", sa.String(128), nullable=True),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("total_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("discount_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_with_disc", sa.Float(), nullable=False, server_default="0"),
        sa.Column("for_pay", sa.Float(), nullable=False, server_default="0"),
        sa.Column("warehouse_name", sa.String(255), nullable=True),
        sa.Column("region_name", sa.String(255), nullable=True),
        sa.Column("sale_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_change_date", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "srid", name="uq_sales_user_srid"),
    )
    op.create_index("ix_sales_user_id", "sales", ["user_id"])
    op.create_index("ix_sales_srid", "sales", ["srid"])
    op.create_index("ix_sales_nm_id", "sales", ["nm_id"])
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("srid", sa.String(128), nullable=False),
        sa.Column("nm_id", sa.BigInteger(), nullable=True),
        sa.Column("supplier_article", sa.String(128), nullable=True),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("total_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("discount_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("price_with_disc", sa.Float(), nullable=False, server_default="0"),
        sa.Column("warehouse_name", sa.String(255), nullable=True),
        sa.Column("region_name", sa.String(255), nullable=True),
        sa.Column("is_cancel", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_change_date", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "srid", name="uq_orders_user_srid"),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_srid", "orders", ["srid"])
    op.create_index("ix_orders_nm_id", "orders", ["nm_id"])
    op.create_index("ix_orders_order_date", "orders", ["order_date"])

    op.create_table(
        "stocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("nm_id", sa.BigInteger(), nullable=True),
        sa.Column("supplier_article", sa.String(128), nullable=True),
        sa.Column("barcode", sa.String(64), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("subject", sa.String(255), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("tech_size", sa.String(64), nullable=True),
        sa.Column("warehouse_name", sa.String(255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_full", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("in_way_to_client", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("in_way_from_client", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("discount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_change_date", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "nm_id",
            "warehouse_name",
            "barcode",
            name="uq_stocks_user_nm_wh_barcode",
        ),
    )
    op.create_index("ix_stocks_user_id", "stocks", ["user_id"])
    op.create_index("ix_stocks_nm_id", "stocks", ["nm_id"])


def downgrade() -> None:
    op.drop_table("stocks")
    op.drop_table("orders")
    op.drop_table("sales")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
