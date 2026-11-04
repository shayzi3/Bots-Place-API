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
    auth_from: UserAuthEnum
    is_verified: bool
    created_at: datetime
