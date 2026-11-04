class EmailAlreadyExistsError(Exception):
    """Raised when a user with the given email already exists."""

    def __init__(self, email: str) -> None:
        super().__init__(f"User with email {email!r} already exists")
        self.email = email


class LoginNotAllowedError(Exception):
    """Raised when login is requested for an unknown or unverified user."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Login is not allowed for {email!r}")
        self.email = email


class InvalidEmailCodeError(Exception):
    """Raised when the email confirmation code is missing, wrong or expired."""


class InvalidTokenError(Exception):
    """Raised when a JWT token is missing, malformed or expired."""
