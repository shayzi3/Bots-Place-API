import pytest
from pydantic import ValidationError

from bots_place.domain.commands import (
    ConfirmLoginCommand,
    ConfirmRegistrationCommand,
    RegisterUserCommand,
    RequestLoginCodeCommand,
)


@pytest.mark.parametrize(
    "email",
    ["not-an-email", "a@", "@b.c", "a b@c.d", "a@b", ""],
)
def test_register_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        RegisterUserCommand(email=email, username="user")


def test_register_rejects_missing_username() -> None:
    with pytest.raises(ValidationError):
        RegisterUserCommand(email="a@b.c")


def test_register_accepts_valid_input() -> None:
    command = RegisterUserCommand(email="a@b.c", username="user")
    assert command.email == "a@b.c"
    assert command.username == "user"


@pytest.mark.parametrize("email", ["nope", "a@", "", "a@b"])
def test_request_login_rejects_invalid_email(email: str) -> None:
    with pytest.raises(ValidationError):
        RequestLoginCodeCommand(email=email)


def test_confirm_login_requires_code() -> None:
    with pytest.raises(ValidationError):
        ConfirmLoginCommand(email="a@b.c")


def test_confirm_registration_requires_code() -> None:
    with pytest.raises(ValidationError):
        ConfirmRegistrationCommand(email="a@b.c")
