from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserProfileSchema(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


class ChangeUsernameSchema(BaseModel):
    username: str


class ChangeUserEmailSchema(BaseModel):
    email: EmailStr
