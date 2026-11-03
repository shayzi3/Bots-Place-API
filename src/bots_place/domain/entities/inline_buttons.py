from datetime import datetime

from pydantic import BaseModel, Field


class InlineButtonModel(BaseModel):
    text: str = Field(max_length=32)
    data: str = Field(max_length=128)
    url: str | None = Field(max_length=256)


class InlineButtonsModel(BaseModel):
    """Model for payload in update. Type: UpdateTypeEnum.BUTTON. Create by UpdateFromEnum.BOT"""

    buttons: list[list[InlineButtonModel]]


class InlineButtonPressedBaseModel(BaseModel):
    """Model for payload in update. Type: UpdateTypeEnum.BUTTON_PRESSED. Create by UpdateFromEnum.USER"""

    id: int
    user_id: int
    chat_id: int
    update_id: int
    inline_button: InlineButtonModel
    pressed_at: datetime
