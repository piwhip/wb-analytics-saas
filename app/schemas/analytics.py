from datetime import date

from pydantic import BaseModel


class SummaryOut(BaseModel):
    period_from: date
    period_to: date
    sales_count: int
    sales_revenue: float
    for_pay_total: float
    orders_count: int
    orders_revenue: float
    cancel_count: int
    avg_check: float


class DayPoint(BaseModel):
    day: date
    sales_count: int
    revenue: float


class SalesDynamicsOut(BaseModel):
    period_from: date
    period_to: date
    points: list[DayPoint]


class TopProduct(BaseModel):
    nm_id: int | None
    supplier_article: str | None
    brand: str | None
    subject: str | None
    sales_count: int
    revenue: float


class TopProductsOut(BaseModel):
    period_from: date
    period_to: date
    products: list[TopProduct]


class StockItem(BaseModel):
    nm_id: int | None
    supplier_article: str | None
    brand: str | None
    subject: str | None
    warehouse_name: str | None
    quantity: int


class LowStockOut(BaseModel):
    threshold: int
    items: list[StockItem]


class SyncResult(BaseModel):
    sales_synced: int
    orders_synced: int
    stocks_synced: int
