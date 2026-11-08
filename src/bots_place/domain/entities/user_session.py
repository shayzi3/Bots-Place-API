from datetime import datetime

from pydantic import BaseModel


class UserSessionBaseModel(BaseModel):
    id: int
    user_id: int
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
