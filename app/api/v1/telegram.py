import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.models import User
from app.services.telegram import get_bot_username, send_message

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/link")
async def create_link(user: CurrentUser, db: DBSession) -> dict[str, str]:
    """Сгенерировать deep-link для привязки Telegram через нажатие «Старт» в боте."""
    bot = await get_bot_username()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="На сервере не настроен TELEGRAM_BOT_TOKEN",
        )
    token = secrets.token_urlsafe(16)
    user.tg_link_token = token
    await db.commit()
    return {
        "deep_link": f"https://t.me/{bot}?start={token}",
        "bot_username": bot,
    }


@router.post("/webhook", include_in_schema=False)
async def webhook(
    request: Request,
    db: DBSession,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    # Проверяем, что запрос действительно от Telegram (секрет из setWebhook).
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    update: dict[str, Any] = await request.json()
    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    username = chat.get("username")
    text = (message.get("text") or "").strip()

    if not chat_id or not text.startswith("/start"):
        return {"ok": True}

    parts = text.split(maxsplit=1)
    token = parts[1].strip() if len(parts) > 1 else ""

    if not token:
        await send_message(
            chat_id,
            "👋 Чтобы подключить уведомления, откройте бота из дашборда "
            "WB Analytics кнопкой «Подключить Telegram».",
        )
        return {"ok": True}

    user = await db.scalar(select(User).where(User.tg_link_token == token))
    if not user:
        await send_message(chat_id, "❌ Ссылка устарела. Сгенерируйте новую в дашборде.")
        return {"ok": True}

    user.telegram_chat_id = chat_id
    user.telegram_username = username
    user.tg_link_token = None
    await db.commit()

    await send_message(
        chat_id,
        "✅ <b>Готово!</b> Аккаунт привязан — будете получать сводки и алерты "
        "о низких остатках.",
    )
    return {"ok": True}
