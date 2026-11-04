from datetime import UTC, datetime

from bots_place.domain.entities.email_code import EmailCodeBaseModel
from bots_place.infrastructure.repository.base.repositories.email_code import (
    BaseEmailCodeRepository,
)
from bots_place.infrastructure.repository.expressions import Model
from bots_place.infrastructure.repository.sqlalchemy.models.email_code import (
    EmailCode,
)

from .base import SqlAlchemyBaseRepository


class EmailCodeRepository(
    SqlAlchemyBaseRepository[EmailCode, EmailCodeBaseModel],
    BaseEmailCodeRepository,
):
    model = EmailCode
    entity = EmailCodeBaseModel

    async def get_active(self, email: str, purpose: str) -> EmailCodeBaseModel | None:
        codes = await self.get_all(
            Model.email == email,
            Model.purpose == purpose,
            Model.used_at.is_(None),
            Model.expires_at > datetime.now(UTC),
            order_by=Model.created_at.desc(),
            limit=1,
        )
        return codes[0] if codes else None
