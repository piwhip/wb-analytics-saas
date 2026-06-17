from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Sale(Base):
    """Запись о продаже из WB Statistics API (/api/v1/supplier/sales)."""

    __tablename__ = "sales"
    __table_args__ = (UniqueConstraint("user_id", "srid", name="uq_sales_user_srid"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    srid: Mapped[str] = mapped_column(String(128), index=True)
    sale_id: Mapped[str | None] = mapped_column(String(64), default=None)
    nm_id: Mapped[int | None] = mapped_column(BigInteger, index=True, default=None)
    supplier_article: Mapped[str | None] = mapped_column(String(128), default=None)
    barcode: Mapped[str | None] = mapped_column(String(64), default=None)
    brand: Mapped[str | None] = mapped_column(String(255), default=None)
    subject: Mapped[str | None] = mapped_column(String(255), default=None)
    category: Mapped[str | None] = mapped_column(String(255), default=None)

    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0)
    price_with_disc: Mapped[float] = mapped_column(Float, default=0.0)
    for_pay: Mapped[float] = mapped_column(Float, default=0.0)

    warehouse_name: Mapped[str | None] = mapped_column(String(255), default=None)
    region_name: Mapped[str | None] = mapped_column(String(255), default=None)

    sale_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_change_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    user: Mapped["User"] = relationship(back_populates="sales")  # noqa: F821


class Order(Base):
    """Запись о заказе из WB Statistics API (/api/v1/supplier/orders)."""

    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("user_id", "srid", name="uq_orders_user_srid"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    srid: Mapped[str] = mapped_column(String(128), index=True)
    nm_id: Mapped[int | None] = mapped_column(BigInteger, index=True, default=None)
    supplier_article: Mapped[str | None] = mapped_column(String(128), default=None)
    barcode: Mapped[str | None] = mapped_column(String(64), default=None)
    brand: Mapped[str | None] = mapped_column(String(255), default=None)
    subject: Mapped[str | None] = mapped_column(String(255), default=None)
    category: Mapped[str | None] = mapped_column(String(255), default=None)

    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0)
    price_with_disc: Mapped[float] = mapped_column(Float, default=0.0)

    warehouse_name: Mapped[str | None] = mapped_column(String(255), default=None)
    region_name: Mapped[str | None] = mapped_column(String(255), default=None)
    is_cancel: Mapped[int] = mapped_column(Integer, default=0)

    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_change_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    user: Mapped["User"] = relationship(back_populates="orders")  # noqa: F821
