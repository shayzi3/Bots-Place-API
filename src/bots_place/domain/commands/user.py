from pydantic import BaseModel, EmailStr


class RegisterUserCommand(BaseModel):
    email: EmailStr
    username: str


class ConfirmRegistrationCommand(BaseModel):
    email: EmailStr
    code: str
