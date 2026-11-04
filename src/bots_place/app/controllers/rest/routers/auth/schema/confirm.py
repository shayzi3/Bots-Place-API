from pydantic import BaseModel


class ConfirmCodeForm(BaseModel):
    code: str
