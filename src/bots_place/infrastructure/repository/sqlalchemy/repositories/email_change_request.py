from bots_place.domain.entities.email_change_request import (
    EmailChangeRequestBaseModel,
)
from bots_place.infrastructure.repository.base.repositories.email_change_request import (
    BaseEmailChangeRequestRepository,
)
from bots_place.infrastructure.repository.expressions import Model
from bots_place.infrastructure.repository.sqlalchemy.models.email_change_request import (
    EmailChangeRequest,
)

from .base import SqlAlchemyBaseRepository


class EmailChangeRequestRepository(
    SqlAlchemyBaseRepository[EmailChangeRequest, EmailChangeRequestBaseModel],
    BaseEmailChangeRequestRepository,
):
    model = EmailChangeRequest
    entity = EmailChangeRequestBaseModel

    async def get_latest_for_user(
        self, user_id: int
    ) -> EmailChangeRequestBaseModel | None:
        requests = await self.get_all(
            Model.user_id == user_id,
            order_by=Model.created_at.desc(),
            limit=1,
        )
        return requests[0] if requests else None
