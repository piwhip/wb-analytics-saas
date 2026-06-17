from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.schemas.analytics import (
    LowStockOut,
    SalesDynamicsOut,
    SummaryOut,
    TopProductsOut,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _default_range(dt_from: date | None, dt_to: date | None) -> tuple[date, date]:
    to = dt_to or date.today()
    frm = dt_from or (to - timedelta(days=30))
    return frm, to


@router.get("/summary", response_model=SummaryOut)
async def summary(
    user: CurrentUser,
    db: DBSession,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
) -> SummaryOut:
    frm, to = _default_range(date_from, date_to)
    return await AnalyticsService(db).summary(user.id, frm, to)


@router.get("/sales-dynamics", response_model=SalesDynamicsOut)
async def sales_dynamics(
    user: CurrentUser,
    db: DBSession,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
) -> SalesDynamicsOut:
    frm, to = _default_range(date_from, date_to)
    return await AnalyticsService(db).sales_dynamics(user.id, frm, to)


@router.get("/top-products", response_model=TopProductsOut)
async def top_products(
    user: CurrentUser,
    db: DBSession,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
) -> TopProductsOut:
    frm, to = _default_range(date_from, date_to)
    return await AnalyticsService(db).top_products(user.id, frm, to, limit)


@router.get("/low-stock", response_model=LowStockOut)
async def low_stock(
    user: CurrentUser,
    db: DBSession,
    threshold: int = Query(5, ge=0, le=10000),
) -> LowStockOut:
    return await AnalyticsService(db).low_stock(user.id, threshold)
