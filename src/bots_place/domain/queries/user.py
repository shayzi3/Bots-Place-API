from pydantic import BaseModel


class GetUserByIdQuery(BaseModel):
    user_id: int
