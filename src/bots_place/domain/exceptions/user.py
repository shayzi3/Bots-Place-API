from .base import AppError


class EmailAlreadyExistsError(AppError):
    """Raised when a user with the given email already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email {email!r} already exists")
        self.email = email


class LoginNotAllowedError(AppError):
    """Raised when login is requested for an unknown or unverified user."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Login is not allowed for {email!r}")
        self.email = email


class InvalidEmailCodeError(AppError):
    """Raised when the email confirmation code is missing, wrong or expired."""


class InvalidTokenError(AppError):
    """Raised when a JWT token is missing, malformed or expired."""


class ResendNotAllowedError(AppError):
    """Raised when a code cannot be resent for the given email and purpose."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Code resend is not allowed for {email!r}")
        self.email = email


class ResendCooldownError(AppError):
    """Raised when a code is requested again before the cooldown has passed."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Retry after {retry_after} seconds")
        self.retry_after = retry_after
