from pydantic import BaseModel


class GetUserBySessionQuery(BaseModel):
    token: str
