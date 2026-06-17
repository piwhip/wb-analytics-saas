from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DBSession
from app.core.security import encrypt_token
from app.schemas.user import TelegramLinkIn, UserOut, WBTokenIn
from app.services.wb_client import WBClient

router = APIRouter(prefix="/users", tags=["users"])


def _to_out(user) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        wb_token_connected=bool(user.wb_token_encrypted),
        telegram_chat_id=user.telegram_chat_id,
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return _to_out(user)


@router.put("/me/wb-token", response_model=UserOut)
async def connect_wb_token(data: WBTokenIn, user: CurrentUser, db: DBSession) -> UserOut:

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
