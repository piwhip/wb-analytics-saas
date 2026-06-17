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


class Stock(Base):
    """Снимок остатков из WB Statistics API (/api/v1/supplier/stocks).

    Хранится по последнему синку на пару (nm_id, warehouse, barcode).
    """

    __tablename__ = "stocks"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "nm_id",
            "warehouse_name",
            "barcode",
            name="uq_stocks_user_nm_wh_barcode",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    nm_id: Mapped[int | None] = mapped_column(BigInteger, index=True, default=None)
    supplier_article: Mapped[str | None] = mapped_column(String(128), default=None)
    barcode: Mapped[str | None] = mapped_column(String(64), default=None)
    brand: Mapped[str | None] = mapped_column(String(255), default=None)
    subject: Mapped[str | None] = mapped_column(String(255), default=None)
    category: Mapped[str | None] = mapped_column(String(255), default=None)
    tech_size: Mapped[str | None] = mapped_column(String(64), default=None)

    warehouse_name: Mapped[str | None] = mapped_column(String(255), default=None)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    quantity_full: Mapped[int] = mapped_column(Integer, default=0)
    in_way_to_client: Mapped[int] = mapped_column(Integer, default=0)
    in_way_from_client: Mapped[int] = mapped_column(Integer, default=0)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    discount: Mapped[float] = mapped_column(Float, default=0.0)

    last_change_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    user: Mapped["User"] = relationship(back_populates="stocks")  # noqa: F821
