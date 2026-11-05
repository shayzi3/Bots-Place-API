from pydantic import BaseModel


class RetryAfterSchema(BaseModel):
    retry_after: int
