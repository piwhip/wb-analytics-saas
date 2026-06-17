from datetime import UTC, date, datetime

from app.models import Sale, Stock, User
from app.services.analytics_service import AnalyticsService


async def _make_user(session) -> User:
    user = User(email="x@y.com", hashed_password="x")
    session.add(user)
    await session.flush()
    return user


def _sale(user_id, srid, nm_id, price, day) -> Sale:
    return Sale(
        user_id=user_id,
        srid=srid,
        nm_id=nm_id,
        supplier_article=f"ART-{nm_id}",
        brand="BrandA",
        subject="Футболка",
        price_with_disc=price,
        for_pay=price * 0.8,
        sale_date=datetime(2026, 6, day, 12, 0, tzinfo=UTC),
    )


async def test_summary_and_avg_check(db_session):
    user = await _make_user(db_session)
    db_session.add_all(
        [
            _sale(user.id, "s1", 100, 1000.0, 10),
            _sale(user.id, "s2", 100, 2000.0, 10),
            _sale(user.id, "s3", 200, 3000.0, 11),
        ]
    )
    await db_session.commit()

    svc = AnalyticsService(db_session)
    summary = await svc.summary(user.id, date(2026, 6, 1), date(2026, 6, 30))

    assert summary.sales_count == 3
    assert summary.sales_revenue == 6000.0
    assert summary.for_pay_total == 4800.0
    assert summary.avg_check == 2000.0


async def test_sales_dynamics_groups_by_day(db_session):
    user = await _make_user(db_session)
    db_session.add_all(
        [
            _sale(user.id, "s1", 100, 1000.0, 10),
            _sale(user.id, "s2", 100, 500.0, 10),
            _sale(user.id, "s3", 200, 3000.0, 11),
        ]
    )
    await db_session.commit()

    svc = AnalyticsService(db_session)
    dyn = await svc.sales_dynamics(user.id, date(2026, 6, 1), date(2026, 6, 30))

    assert len(dyn.points) == 2
    day10 = next(p for p in dyn.points if p.day == date(2026, 6, 10))
    assert day10.sales_count == 2
    assert day10.revenue == 1500.0


async def test_top_products_sorted_by_revenue(db_session):
    user = await _make_user(db_session)
    db_session.add_all(
        [
            _sale(user.id, "s1", 100, 1000.0, 10),
            _sale(user.id, "s2", 200, 5000.0, 10),
            _sale(user.id, "s3", 200, 1000.0, 11),
        ]
    )
    await db_session.commit()

    svc = AnalyticsService(db_session)
    top = await svc.top_products(user.id, date(2026, 6, 1), date(2026, 6, 30), limit=10)

    assert top.products[0].nm_id == 200
    assert top.products[0].revenue == 6000.0
    assert top.products[1].nm_id == 100


async def test_low_stock_threshold(db_session):
    user = await _make_user(db_session)
    db_session.add_all(
        [
            Stock(user_id=user.id, nm_id=1, barcode="b1", warehouse_name="Коледино", quantity=2),
            Stock(user_id=user.id, nm_id=2, barcode="b2", warehouse_name="Коледино", quantity=50),
            Stock(user_id=user.id, nm_id=3, barcode="b3", warehouse_name="Казань", quantity=0),
        ]
    )
    await db_session.commit()

    svc = AnalyticsService(db_session)
    low = await svc.low_stock(user.id, threshold=5)

    nm_ids = {item.nm_id for item in low.items}
    assert nm_ids == {1, 3}
