from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ModalFieldTypeEnum(StrEnum):
    INT = "integer"
    STR = "string"


class ModalFieldModel(BaseModel):
    type: ModalFieldTypeEnum
    placeholder: str | None = None
    max_length: int | None = None
    choices: list[str] | None = None


class ModalModel(BaseModel):
    """Model for payload in update. Type: UpdateTypeEnum.MODAL. Create by UpdateFromEnum.BOT"""

    title: str
    description: str | None = None
    created_at: datetime


class ModalWithFieldsModel(ModalModel):
    fields: list[ModalFieldModel]


class ModalSubmittedFieldModel(ModalFieldModel):
    data: str | int


class ModalSubmittedModel(ModalModel):
    """Model for payload in update. Type: UpdateTypeEnum.MODAL_SUBMITTED. Create by UpdateFromEnum.USER"""

    user_id: int
    chat_id: int
    update_id: int
    submitted_at: datetime

    submitted_fields: list[ModalSubmittedFieldModel]
