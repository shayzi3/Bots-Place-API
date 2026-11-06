from datetime import UTC, datetime, timedelta

import jwt
import pytest

from bots_place.app.security.codes import generate_code
from bots_place.app.security.tokens import TokenService
from bots_place.config.env import JwtSettings
from bots_place.domain.exceptions.user import InvalidTokenError

SECRET = "x" * 32


def make_service(
    *, access_ttl_minutes: int = 60, pending_ttl_minutes: int = 15
) -> TokenService:
    settings = JwtSettings(
        secret="x" * 32,
        algorithm="HS256",
        access_ttl_minutes=access_ttl_minutes,
        pending_ttl_minutes=pending_ttl_minutes,
    )
    return TokenService(settings)


def test_access_token_roundtrip() -> None:
    service = make_service()
    payload = service.decode_access(service.create_access(42, "a@b.c"))
    assert payload.user_id == 42
    assert payload.email == "a@b.c"


def test_tampered_token_is_rejected() -> None:
    service = make_service()
    with pytest.raises(InvalidTokenError):
        service.decode_access(service.create_access(1, "a@b.c") + "x")


@pytest.mark.parametrize("token", ["", "not-a-jwt", "a.b.c"])
def test_malformed_token_is_rejected(token: str) -> None:
    service = make_service()
    with pytest.raises(InvalidTokenError):
        service.decode_access(token)


def test_expired_access_token_is_rejected() -> None:
    service = make_service(access_ttl_minutes=-1)
    token = service.create_access(1, "a@b.c")
    with pytest.raises(InvalidTokenError):
        service.decode_access(token)


def test_token_signed_with_other_secret_is_rejected() -> None:
    foreign = TokenService(
        JwtSettings(
            secret="y" * 32,
            algorithm="HS256",
            access_ttl_minutes=60,
            pending_ttl_minutes=15,
        )
    )
    token = foreign.create_access(1, "a@b.c")
    with pytest.raises(InvalidTokenError):
        make_service().decode_access(token)


def test_unsigned_alg_none_token_is_rejected() -> None:
    token = jwt.encode(
        {
            "type": "access",
            "sub": "1",
            "email": "a@b.c",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        None,
        algorithm="none",
    )
    with pytest.raises(InvalidTokenError):
        make_service().decode_access(token)


def test_access_token_without_subject_is_rejected() -> None:
    token = jwt.encode(
        {
            "type": "access",
            "email": "a@b.c",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET,
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        make_service().decode_access(token)


def test_access_token_with_non_numeric_subject_is_rejected() -> None:
    token = jwt.encode(
        {
            "type": "access",
            "sub": "not-a-number",
            "email": "a@b.c",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET,
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        make_service().decode_access(token)


def test_ttl_seconds() -> None:
    service = make_service(access_ttl_minutes=2, pending_ttl_minutes=1)
    assert service.access_ttl_seconds == 120
    assert service.confirmation_ttl_seconds == 60


def test_generate_code_is_six_digits() -> None:
    code = generate_code()
    assert len(code) == 6
    assert code.isdigit()


def test_generate_code_is_random() -> None:
    assert len({generate_code() for _ in range(20)}) > 1
