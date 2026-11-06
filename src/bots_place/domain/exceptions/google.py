from .base import AppError


class GoogleAuthError(AppError):
    """Base class for Google sign-in failures."""


class GoogleAuthFailedError(GoogleAuthError):
    """Raised when the Google sign-in flow cannot be completed."""


class GoogleEmailNotVerifiedError(GoogleAuthError):
    """Raised when the Google account email is not verified."""
