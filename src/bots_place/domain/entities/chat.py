from datetime import datetime

from pydantic import BaseModel


class ChatModel(BaseModel):
    id: int
    bot_id: int
    user_id: int
    created_at: datetime
