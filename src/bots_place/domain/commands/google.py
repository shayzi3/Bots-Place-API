from pydantic import BaseModel, EmailStr


class GoogleLoginCommand(BaseModel):
    email: EmailStr
    username: str
