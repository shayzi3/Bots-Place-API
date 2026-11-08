from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from bots_place.domain.commands import ChangeUsernameCommand
from bots_place.domain.entities.user import UserAuthEnum, UserBaseModel
from bots_place.domain.exceptions import UserNotFoundError
from bots_place.infrastructure.commands import ChangeUsernameHandler


@pytest.fixture
def uow() -> MagicMock:
    mock = MagicMock()
    mock.users = AsyncMock()
    return mock


def make_user(username: str) -> UserBaseModel:
    return UserBaseModel(
        id=1,
        email="user@example.com",
        username=username,
        auth_from=UserAuthEnum.BASIC,
        is_verified=True,
        created_at=datetime.now(UTC),
    )


async def test_change_username_updates_user(uow: MagicMock) -> None:
    updated = make_user("neo")
    uow.users.update.return_value = updated
    handler = ChangeUsernameHandler(uow)

    result = await handler.handle(ChangeUsernameCommand(user_id=1, new_username="neo"))

    assert result == updated
    uow.users.update.assert_awaited_once()
    _, kwargs = uow.users.update.call_args
    assert kwargs["obj_in"] == {"username": "neo"}
    assert kwargs["auto_commit"] is True


async def test_change_username_raises_for_missing_user(uow: MagicMock) -> None:
    uow.users.update.return_value = None
    handler = ChangeUsernameHandler(uow)

    with pytest.raises(UserNotFoundError):
        await handler.handle(ChangeUsernameCommand(user_id=99, new_username="neo"))
