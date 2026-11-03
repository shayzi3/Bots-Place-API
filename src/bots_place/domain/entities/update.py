from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class UpdateFromEnum(StrEnum):
    USER = "user"
    BOT = "bot"


class UpdateTypeEnum(StrEnum):
    MESSAGE = "message"
    BUTTON = "button"
    BUTTON_PRESSED = "button_pressed"
    MODAL = "modal"
    MODAL_SUBMITTED = "modal_submitted"


class UpdateBaseModel(BaseModel):
    id: int
    sender_user_id: int | None
    sender_bot_id: int | None
    chat_id: int
    type: UpdateTypeEnum
    update_from: UpdateFromEnum
    payload: dict
    processed: bool
    created_at: datetime
