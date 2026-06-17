import random
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, DBSession
from app.models import Order, Sale, Stock

router = APIRouter(prefix="/demo", tags=["demo"])

_PRODUCTS = [
    (101, "TSHIRT-WHITE-M", "AuraWear", "Футболка"),
    (102, "HOODIE-BLK-L", "AuraWear", "Худи"),
    (103, "JEANS-BLUE-32", "DenimCo", "Джинсы"),
    (104, "CAP-RED", "StreetLine", "Кепка"),
    (105, "SOCKS-PACK5", "BasicLab", "Носки"),
]
_WAREHOUSES = ["Коледино", "Казань", "Электросталь", "Тула"]
_REGIONS = ["Москва", "Санкт-Петербург", "Краснодар", "Новосибирск"]


@router.post("/seed")
async def seed_demo_data(
    user: CurrentUser,
    db: DBSession,
    days: int = Query(30, ge=1, le=90),
    sales_per_day: int = Query(8, ge=1, le=100),
):
    """Заполнить аккаунт случайными продажами/заказами/остатками за период.

    Удобно для демонстрации аналитики без реального кабинета Wildberries.
    """
    now = datetime.now(UTC)
    rnd = random.Random(user.id)

    sales: list[Sale] = []
    orders: list[Order] = []
    counter = 0

    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        for _ in range(rnd.randint(1, sales_per_day)):
            counter += 1
            nm_id, article, brand, subject = rnd.choice(_PRODUCTS)
            price = rnd.choice([799, 1299, 1899, 2499, 3499])
            discount = rnd.choice([0, 10, 15, 25])
            price_with_disc = round(price * (1 - discount / 100), 2)
            wh = rnd.choice(_WAREHOUSES)
            region = rnd.choice(_REGIONS)

            orders.append(
                Order(
                    user_id=user.id,
                    srid=f"demo-o-{user.id}-{counter}",
                    nm_id=nm_id,
                    supplier_article=article,
                    brand=brand,
                    subject=subject,
                    total_price=price,
                    discount_percent=discount,
                    price_with_disc=price_with_disc,
                    warehouse_name=wh,
                    region_name=region,
                    is_cancel=1 if rnd.random() < 0.07 else 0,
                    order_date=day,
                    last_change_date=day,
                )
            )
            # Часть заказов превращается в продажи.
            if rnd.random() < 0.8:
                sales.append(
                    Sale(
                        user_id=user.id,
                        srid=f"demo-s-{user.id}-{counter}",
                        sale_id=f"S{counter}",
                        nm_id=nm_id,
                        supplier_article=article,
                        brand=brand,
                        subject=subject,
                        total_price=price,
                        discount_percent=discount,
                        price_with_disc=price_with_disc,
                        for_pay=round(price_with_disc * 0.83, 2),
                        warehouse_name=wh,
                        region_name=region,
                        sale_date=day,
                        last_change_date=day,
                    )
                )

    stocks = [
        Stock(
            user_id=user.id,
            nm_id=nm_id,
            supplier_article=article,
            barcode=f"200000{nm_id}",
            brand=brand,
            subject=subject,
            tech_size=rnd.choice(["S", "M", "L", "XL", "0"]),
            warehouse_name=rnd.choice(_WAREHOUSES),
            quantity=rnd.choice([0, 1, 3, 5, 12, 40, 120]),
            quantity_full=rnd.randint(0, 150),
            last_change_date=now,
        )
        for nm_id, article, brand, subject in _PRODUCTS
    ]

    db.add_all(orders)
    db.add_all(sales)
    db.add_all(stocks)
    await db.commit()

    return {
        "seeded": True,
        "orders": len(orders),
        "sales": len(sales),
        "stocks": len(stocks),
        "period_days": days,
    }
