from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DBSession
from app.core.config import settings
from app.core.security import encrypt_token
from app.schemas.user import TelegramLinkIn, UserOut, WBTokenIn
from app.services.telegram import send_message
from app.services.wb_client import WBClient

router = APIRouter(prefix="/users", tags=["users"])


def _to_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        wb_token_connected=bool(user.wb_token_encrypted),
        telegram_chat_id=user.telegram_chat_id,
        telegram_username=user.telegram_username,
        is_demo=user.is_demo,
        is_subscribed=user.is_subscribed,
        analyses_used=user.analyses_used,
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return _to_out(user)


@router.put("/me/wb-token", response_model=UserOut)
async def connect_wb_token(data: WBTokenIn, user: CurrentUser, db: DBSession) -> UserOut:
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Зарегистрируйтесь, чтобы подключить свой кабинет Wildberries",
        )
    async with WBClient(data.wb_token) as client:
        if not await client.ping():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="WB token rejected by Wildberries API",
            )
    user.wb_token_encrypted = encrypt_token(data.wb_token)
    await db.commit()
    await db.refresh(user)
    return _to_out(user)


@router.put("/me/telegram", response_model=UserOut)
async def link_telegram(data: TelegramLinkIn, user: CurrentUser, db: DBSession) -> UserOut:
    user.telegram_chat_id = data.telegram_chat_id
    await db.commit()
    await db.refresh(user)
    return _to_out(user)


@router.post("/me/telegram/test")
async def test_telegram(user: CurrentUser) -> dict[str, bool]:
    if not user.telegram_chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сначала привяжите Telegram chat_id",
        )
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="На сервере не настроен TELEGRAM_BOT_TOKEN — уведомления отключены",
        )
    ok = await send_message(
        user.telegram_chat_id,
        "✅ <b>WB Analytics</b>\nТестовое уведомление — всё работает!",
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось отправить. Проверьте chat_id и что вы написали боту /start",
        )
    return {"sent": True}
