"""Celery-задачи. Бизнес-логика async, исполняется через asyncio.run."""

from __future__ import annotations

import asyncio
from datetime import date, timedelta

from sqlalchemy import select

from app.core.database import get_sessionmaker
from app.models import User
from app.services.analytics_service import AnalyticsService
from app.services.sync_service import SyncService
from app.services.telegram import send_message
from app.workers.celery_app import celery_app


def _run(coro):
    return asyncio.run(coro)


async def _sync_user(user_id: int, days_back: int) -> dict[str, int]:
    async with get_sessionmaker()() as session:
        user = await session.get(User, user_id)
        if user is None or not user.wb_token_encrypted:
            return {"sales_synced": 0, "orders_synced": 0, "stocks_synced": 0}
        return await SyncService(session).sync_user(user, days_back=days_back)


@celery_app.task(name="app.workers.tasks.sync_user_task", bind=True, max_retries=3)
def sync_user_task(self, user_id: int, days_back: int = 30) -> dict[str, int]:
    try:
        return _run(_sync_user(user_id, days_back))
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=60) from exc


async def _all_user_ids() -> list[int]:
    async with get_sessionmaker()() as session:
        rows = await session.scalars(
            select(User.id).where(User.is_active.is_(True), User.wb_token_encrypted.is_not(None))
        )
        return list(rows)


@celery_app.task(name="app.workers.tasks.sync_all_users_task")
def sync_all_users_task(days_back: int = 2) -> dict[str, int]:
    user_ids = _run(_all_user_ids())
    for uid in user_ids:
        sync_user_task.delay(uid, days_back)
    return {"scheduled_users": len(user_ids)}


async def _low_stock_alerts(threshold: int) -> int:
    sent = 0
    async with get_sessionmaker()() as session:
        users = await session.scalars(
            select(User).where(User.is_active.is_(True), User.telegram_chat_id.is_not(None))
        )
        for user in users:
            report = await AnalyticsService(session).low_stock(user.id, threshold)
            if not report.items:
                continue
            lines = [f"⚠️ <b>Низкие остатки</b> (≤ {threshold} шт.):", ""]
            for item in report.items[:20]:
                name = item.supplier_article or item.subject or item.nm_id or "—"
                lines.append(f"• {name} — {item.quantity} шт. ({item.warehouse_name})")
            if await send_message(user.telegram_chat_id, "\n".join(lines)):
                sent += 1
    return sent


@celery_app.task(name="app.workers.tasks.low_stock_alerts_task")
def low_stock_alerts_task(threshold: int = 5) -> dict[str, int]:
    return {"notifications_sent": _run(_low_stock_alerts(threshold))}


async def _daily_summary() -> int:
    sent = 0
    today = date.today()
    yesterday = today - timedelta(days=1)
    async with get_sessionmaker()() as session:
        users = await session.scalars(
            select(User).where(User.is_active.is_(True), User.telegram_chat_id.is_not(None))
        )
        for user in users:
            s = await AnalyticsService(session).summary(user.id, yesterday, yesterday)
            text = (
                f"📊 <b>Сводка за {yesterday:%d.%m.%Y}</b>\n\n"
                f"Продаж: <b>{s.sales_count}</b> на <b>{s.sales_revenue:,.0f} ₽</b>\n"
                f"К перечислению: <b>{s.for_pay_total:,.0f} ₽</b>\n"
                f"Заказов: <b>{s.orders_count}</b> на <b>{s.orders_revenue:,.0f} ₽</b>\n"
                f"Отмен: <b>{s.cancel_count}</b>\n"
                f"Средний чек: <b>{s.avg_check:,.0f} ₽</b>"
            )
            if await send_message(user.telegram_chat_id, text):
                sent += 1
    return sent


@celery_app.task(name="app.workers.tasks.daily_summary_task")
def daily_summary_task() -> dict[str, int]:
    return {"notifications_sent": _run(_daily_summary())}
