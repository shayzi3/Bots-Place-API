from bots_place.domain.commands import GoogleLoginCommand
from bots_place.domain.entities.user import UserAuthEnum, UserBaseModel
from bots_place.domain.exceptions.google import GoogleAuthFailedError
from bots_place.infrastructure.repository import Model
from bots_place.infrastructure.repository.base import BaseUnitOfWork


class GoogleLoginHandler:
    def __init__(self, uow: BaseUnitOfWork) -> None:
        self._uow = uow

    async def handle(self, command: GoogleLoginCommand) -> UserBaseModel:
        user = await self._uow.users.get_by_email(command.email)
        if user is None:
            return await self._uow.users.create(
                {
                    "email": command.email,
                    "username": command.username,
                    "auth_from": UserAuthEnum.GOOGLE.value,
                    "is_verified": True,
                },
                auto_commit=True,
            )

        updated = await self._uow.users.update(
            Model.email == command.email,
            obj_in={
                "auth_from": UserAuthEnum.GOOGLE.value,
                "is_verified": True,
            },
            auto_commit=True,
        )
        if updated is None:
            raise GoogleAuthFailedError
        return updated
