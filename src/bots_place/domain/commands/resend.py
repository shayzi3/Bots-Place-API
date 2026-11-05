from pydantic import BaseModel, EmailStr

from bots_place.domain.entities.email_code import EmailCodePurposeEnum


class ResendCodeCommand(BaseModel):
    email: EmailStr
    purpose: EmailCodePurposeEnum
