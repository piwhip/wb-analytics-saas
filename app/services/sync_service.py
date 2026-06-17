"""Синхронизация данных WB в локальную БД (idempotent upsert)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_token
from app.models import Order, Sale, Stock, User
from app.services.wb_client import WBClient


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _map_sale(user_id: int, row: dict[str, Any]) -> dict[str, Any] | None:
    srid = row.get("srid") or row.get("saleID")
    sale_dt = _parse_dt(row.get("date"))
    if not srid or sale_dt is None:
        return None
    return {
        "user_id": user_id,
        "srid": str(srid),
        "sale_id": row.get("saleID"),
        "nm_id": row.get("nmId"),
        "supplier_article": row.get("supplierArticle"),
        "barcode": row.get("barcode"),
        "brand": row.get("brand"),
        "subject": row.get("subject"),
        "category": row.get("category"),
        "total_price": row.get("totalPrice") or 0.0,
        "discount_percent": row.get("discountPercent") or 0.0,
        "price_with_disc": row.get("priceWithDisc") or 0.0,
        "for_pay": row.get("forPay") or 0.0,
        "warehouse_name": row.get("warehouseName"),
        "region_name": row.get("regionName"),
        "sale_date": sale_dt,
        "last_change_date": _parse_dt(row.get("lastChangeDate")),
    }


def _map_order(user_id: int, row: dict[str, Any]) -> dict[str, Any] | None:
    srid = row.get("srid")
    order_dt = _parse_dt(row.get("date"))
    if not srid or order_dt is None:
        return None
    return {
        "user_id": user_id,
        "srid": str(srid),
        "nm_id": row.get("nmId"),
        "supplier_article": row.get("supplierArticle"),
        "barcode": row.get("barcode"),
        "brand": row.get("brand"),
        "subject": row.get("subject"),
        "category": row.get("category"),
        "total_price": row.get("totalPrice") or 0.0,
        "discount_percent": row.get("discountPercent") or 0.0,
        "price_with_disc": row.get("priceWithDisc") or 0.0,
        "warehouse_name": row.get("warehouseName"),
        "region_name": row.get("regionName"),
        "is_cancel": 1 if row.get("isCancel") else 0,
        "order_date": order_dt,
        "last_change_date": _parse_dt(row.get("lastChangeDate")),
    }


def _map_stock(user_id: int, row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("nmId") is None and not row.get("barcode"):
        return None
    return {
        "user_id": user_id,
        "nm_id": row.get("nmId"),
        "supplier_article": row.get("supplierArticle"),
        "barcode": row.get("barcode") or "",
        "brand": row.get("brand"),
        "subject": row.get("subject"),
        "category": row.get("category"),
        "tech_size": row.get("techSize"),
        "warehouse_name": row.get("warehouseName") or "",
        "quantity": row.get("quantity") or 0,
        "quantity_full": row.get("quantityFull") or 0,
        "in_way_to_client": row.get("inWayToClient") or 0,
        "in_way_from_client": row.get("inWayFromClient") or 0,
        "price": row.get("Price") or row.get("price") or 0.0,
        "discount": row.get("Discount") or row.get("discount") or 0.0,
        "last_change_date": _parse_dt(row.get("lastChangeDate")),
    }


async def _upsert(session: AsyncSession, model, rows: list[dict], index_elements: list[str]) -> int:
    if not rows:
        return 0
    stmt = insert(model).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in model.__table__.columns
        if c.name not in {"id", "created_at", *index_elements}
    }
    stmt = stmt.on_conflict_do_update(index_elements=index_elements, set_=update_cols)
    await session.execute(stmt)
    return len(rows)


class SyncService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def sync_user(self, user: User, days_back: int = 30) -> dict[str, int]:
        if not user.wb_token_encrypted:
            raise ValueError("WB token is not connected for this user")

        token = decrypt_token(user.wb_token_encrypted)
        date_from = datetime.now(UTC) - timedelta(days=days_back)

        async with WBClient(token) as client:
            sales_raw = await client.get_sales(date_from)
            orders_raw = await client.get_orders(date_from)
            stocks_raw = await client.get_stocks(datetime.now(UTC))

        sales = [m for r in sales_raw if (m := _map_sale(user.id, r))]
        orders = [m for r in orders_raw if (m := _map_order(user.id, r))]
        stocks = self._dedupe_stocks([m for r in stocks_raw if (m := _map_stock(user.id, r))])

        n_sales = await _upsert(self.session, Sale, sales, ["user_id", "srid"])
        n_orders = await _upsert(self.session, Order, orders, ["user_id", "srid"])
        n_stocks = await _upsert(
            self.session,
            Stock,
            stocks,
            ["user_id", "nm_id", "warehouse_name", "barcode"],
        )
        await self.session.commit()

        return {
            "sales_synced": n_sales,
            "orders_synced": n_orders,
            "stocks_synced": n_stocks,
        }

    @staticmethod
    def _dedupe_stocks(rows: list[dict]) -> list[dict]:
        """В одном ответе WB могут быть дубли по ключу — берём последний."""
        seen: dict[tuple, dict] = {}
        for r in rows:
            key = (r["user_id"], r["nm_id"], r["warehouse_name"], r["barcode"])
            seen[key] = r
        return list(seen.values())
