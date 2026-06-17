"""Аналитические запросы поверх сохранённых данных WB."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Sale, Stock
from app.schemas.analytics import (
    DayPoint,
    LowStockOut,
    SalesDynamicsOut,
    StockItem,
    SummaryOut,
    TopProduct,
    TopProductsOut,
)


def _start(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=UTC)


def _end(d: date) -> datetime:
    return datetime.combine(d, time.max, tzinfo=UTC)


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def summary(self, user_id: int, dt_from: date, dt_to: date) -> SummaryOut:
        lo, hi = _start(dt_from), _end(dt_to)

        sales_q = select(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.price_with_disc), 0.0),
            func.coalesce(func.sum(Sale.for_pay), 0.0),
        ).where(Sale.user_id == user_id, Sale.sale_date.between(lo, hi))
        sales_count, sales_revenue, for_pay = (await self.session.execute(sales_q)).one()

        orders_q = select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.price_with_disc), 0.0),
            func.coalesce(func.sum(Order.is_cancel), 0),
        ).where(Order.user_id == user_id, Order.order_date.between(lo, hi))
        orders_count, orders_revenue, cancel_count = (await self.session.execute(orders_q)).one()

        avg_check = (sales_revenue / sales_count) if sales_count else 0.0

        return SummaryOut(
            period_from=dt_from,
            period_to=dt_to,
            sales_count=sales_count,
            sales_revenue=round(float(sales_revenue), 2),
            for_pay_total=round(float(for_pay), 2),
            orders_count=orders_count,
            orders_revenue=round(float(orders_revenue), 2),
            cancel_count=int(cancel_count),
            avg_check=round(float(avg_check), 2),
        )

    async def sales_dynamics(self, user_id: int, dt_from: date, dt_to: date) -> SalesDynamicsOut:
        lo, hi = _start(dt_from), _end(dt_to)
        day = func.date(Sale.sale_date)
        q = (
            select(
                day.label("day"),
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.price_with_disc), 0.0),
            )
            .where(Sale.user_id == user_id, Sale.sale_date.between(lo, hi))
            .group_by(day)
            .order_by(day)
        )
        rows = (await self.session.execute(q)).all()
        points = [DayPoint(day=r[0], sales_count=r[1], revenue=round(float(r[2]), 2)) for r in rows]
        return SalesDynamicsOut(period_from=dt_from, period_to=dt_to, points=points)

    async def top_products(
        self, user_id: int, dt_from: date, dt_to: date, limit: int = 10
    ) -> TopProductsOut:
        lo, hi = _start(dt_from), _end(dt_to)
        revenue = func.coalesce(func.sum(Sale.price_with_disc), 0.0).label("revenue")
        q = (
            select(
                Sale.nm_id,
                func.max(Sale.supplier_article),
                func.max(Sale.brand),
                func.max(Sale.subject),
                func.count(Sale.id),
                revenue,
            )
            .where(Sale.user_id == user_id, Sale.sale_date.between(lo, hi))
            .group_by(Sale.nm_id)
            .order_by(revenue.desc())
            .limit(limit)
        )
        rows = (await self.session.execute(q)).all()
        products = [
            TopProduct(
                nm_id=r[0],
                supplier_article=r[1],
                brand=r[2],
                subject=r[3],
                sales_count=r[4],
                revenue=round(float(r[5]), 2),
            )
            for r in rows
        ]
        return TopProductsOut(period_from=dt_from, period_to=dt_to, products=products)

    async def low_stock(self, user_id: int, threshold: int = 5) -> LowStockOut:

        total = func.sum(cast(Stock.quantity, Integer)).label("qty")
        q = (
            select(
                Stock.nm_id,
                func.max(Stock.supplier_article),
                func.max(Stock.brand),
                func.max(Stock.subject),
                Stock.warehouse_name,
                total,
            )
            .where(Stock.user_id == user_id)
            .group_by(Stock.nm_id, Stock.warehouse_name)
            .having(total <= threshold)
            .order_by(total)
        )
        rows = (await self.session.execute(q)).all()
        items = [
            StockItem(
                nm_id=r[0],
                supplier_article=r[1],
                brand=r[2],
                subject=r[3],
                warehouse_name=r[4],
                quantity=int(r[5] or 0),
            )
            for r in rows
        ]
        return LowStockOut(threshold=threshold, items=items)
