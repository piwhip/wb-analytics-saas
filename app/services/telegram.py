from __future__ import annotations

import httpx

from app.core.config import settings

_API = "https://api.telegram.org"
_bot_username: str | None = None


def _url(method: str) -> str:
    return f"{_API}/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


async def send_message(chat_id: int, text: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(_url("sendMessage"), json=payload)
        return resp.status_code == 200


async def get_bot_username() -> str | None:
    """Имя бота для deep-link (https://t.me/<username>?start=...). Кэшируется."""
    global _bot_username
    if _bot_username:
        return _bot_username
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(_url("getMe"))
    if resp.status_code != 200:
        return None
    _bot_username = resp.json().get("result", {}).get("username")
    return _bot_username


async def set_webhook(url: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN:
        return False
    payload = {
        "url": url,
        "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
        "allowed_updates": ["message"],
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(_url("setWebhook"), json=payload)
        return resp.status_code == 200
