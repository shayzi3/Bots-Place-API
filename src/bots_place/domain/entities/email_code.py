from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class EmailCodePurposeEnum(StrEnum):
    REGISTRATION = "registration"
    LOGIN = "login"


class EmailCodeBaseModel(BaseModel):
    id: int
    email: str
    code: str
    purpose: EmailCodePurposeEnum
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime
