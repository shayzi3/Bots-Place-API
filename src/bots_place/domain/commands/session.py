from pydantic import BaseModel


class CreateSessionCommand(BaseModel):
    user_id: int


class RevokeSessionCommand(BaseModel):
    token: str
