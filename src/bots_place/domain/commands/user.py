from pydantic import BaseModel, EmailStr


class ChangeUsernameCommand(BaseModel):
    user_id: int
    new_username: str


class ChangeUserEmailCommand(BaseModel):
    user_id: int
    new_email: EmailStr
    link_url: str


class UseEmailChangeLinkCommand(BaseModel):
    token: str


class ConfirmEmailChangeCommand(BaseModel):
    user_id: int
    email: str
    code: str
