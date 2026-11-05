import os
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> Path:
    override = os.getenv("BOTS_PLACE_ENV_FILE")
    if override:
        return Path(override)
    return Path(__file__).parent / ".env"


def _get_settings_config_dict(env_prefix: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_file=_get_env_file(),
        env_prefix=env_prefix,
        case_sensitive=False,
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    model_config = _get_settings_config_dict("DB_")

    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    name: str = "bots_place"

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class JwtSettings(BaseSettings):
    model_config = _get_settings_config_dict("JWT_")

    secret: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_ttl_minutes: int = 60 * 24
    pending_ttl_minutes: int = 15


class SmtpSettings(BaseSettings):
    model_config = _get_settings_config_dict("SMTP_")

    host: str = ""
    port: int = 587
    user: str = ""
    password: str = ""
    from_email: str = ""
    # STARTTLS (обычно порт 587)
    use_tls: bool = True
    # implicit SSL (обычно порт 465)
    use_ssl: bool = False
    timeout: int = 30


class CodeSettings(BaseSettings):
    model_config = _get_settings_config_dict("CODE_")

    resend_cooldown_seconds: int = 60
    max_attempts: int = 5


class CookieSettings(BaseSettings):
    model_config = _get_settings_config_dict("COOKIE_")

    secure: bool = False
    domain: str | None = None
    samesite: Literal["lax", "strict", "none"] = "lax"


class Settings(BaseSettings):
    model_config = _get_settings_config_dict("")

    database: DatabaseSettings = DatabaseSettings()
    jwt: JwtSettings = JwtSettings()
    smtp: SmtpSettings = SmtpSettings()
    cookie: CookieSettings = CookieSettings()
    code: CodeSettings = CodeSettings()


settings = Settings()
