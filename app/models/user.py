from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    wb_token_encrypted: Mapped[str | None] = mapped_column(String(512), default=None)

    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, default=None)
    telegram_username: Mapped[str | None] = mapped_column(String(255), default=None)
    tg_link_token: Mapped[str | None] = mapped_column(String(32), default=None, index=True)

    sales: Mapped[list["Sale"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    stocks: Mapped[list["Stock"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
