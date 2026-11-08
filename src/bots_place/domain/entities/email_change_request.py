from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EmailChangeRequestBaseModel(BaseModel):
    id: UUID
    user_id: int
    new_email: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime
