from datetime import datetime

from pydantic import BaseModel


class BotModel(BaseModel):
    id: int
    owner_id: int
    username: str
    description: str
    token: str
    updated_at: datetime
