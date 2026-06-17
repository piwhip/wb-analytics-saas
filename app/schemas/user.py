from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    wb_token_connected: bool = False
    telegram_chat_id: int | None = None


class WBTokenIn(BaseModel):
    wb_token: str = Field(min_length=10, description="WB API token (Statistics)")


class TelegramLinkIn(BaseModel):
    telegram_chat_id: int
