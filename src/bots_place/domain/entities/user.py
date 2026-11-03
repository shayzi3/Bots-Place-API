from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class UserAuthEnum(StrEnum):
    GOOGLE = "google"
    BASIC = "basic"


class UserBaseModel(BaseModel):
    id: int
    email: str
    username: str
    created_at: datetime
    auth_from: UserAuthEnum
