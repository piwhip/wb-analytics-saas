from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    is_active: bool
    wb_token_connected: bool = False
    telegram_chat_id: int | None = None
    telegram_username: str | None = None
    is_demo: bool = False
    is_subscribed: bool = False
    analyses_used: int = 0
    free_analyses_limit: int = 2


class WBTokenIn(BaseModel):
    wb_token: str = Field(min_length=10, description="WB API token (Statistics)")


class TelegramLinkIn(BaseModel):
    telegram_chat_id: int
