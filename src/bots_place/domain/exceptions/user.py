from .base import AppError


class UserError(AppError):
    """Base class for user and authentication failures."""


class EmailAlreadyExistsError(UserError):
    """Raised when a user with the given email already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email {email!r} already exists")
        self.email = email


class LoginNotAllowedError(UserError):
    """Raised when login is requested for an unknown or unverified user."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Login is not allowed for {email!r}")
        self.email = email


class InvalidEmailCodeError(UserError):
    """Raised when the email confirmation code is missing, wrong or expired."""


class UserNotFoundError(UserError):
    """Raised when a user with the given id does not exist."""

    def __init__(self, user_id: int) -> None:
        super().__init__(f"User with id {user_id} not found")
        self.user_id = user_id


class EmailChangeLinkInvalidError(UserError):
    """Raised when an email change link is unknown, expired or already used."""


class InvalidTokenError(UserError):
    """Raised when a JWT token is missing, malformed or expired."""


class ResendNotAllowedError(UserError):
    """Raised when a code cannot be resent for the given email and purpose."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Code resend is not allowed for {email!r}")
        self.email = email


class ResendCooldownError(UserError):
    """Raised when a code is requested again before the cooldown has passed."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Retry after {retry_after} seconds")
        self.retry_after = retry_after
