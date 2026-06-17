"""Минималистичный отправитель уведомлений через Telegram Bot API."""

from __future__ import annotations

import httpx

from app.core.config import settings

_API = "https://api.telegram.org"


async def send_message(chat_id: int, text: str) -> bool:
    """Отправить сообщение пользователю. Возвращает True при успехе."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    url = f"{_API}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        return resp.status_code == 200
