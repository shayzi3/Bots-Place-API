from pydantic import BaseModel, EmailStr


class RequestLoginCodeCommand(BaseModel):
    email: EmailStr


class ConfirmLoginCommand(BaseModel):
    email: EmailStr
    code: str
