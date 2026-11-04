from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_settings_config_dict(env_prefix: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_prefix=env_prefix,
        case_sensitive=False,
        extra="ignore",
    )


class DatabaseSettings(BaseSettings):
    model_config = _get_settings_config_dict("DB_")

    host: str
    port: int
    user: str
    password: str
    name: str

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{quote_plus(self.user)}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class JwtSettings(BaseSettings):
    model_config = _get_settings_config_dict("JWT_")

    secret: str
    algorithm: str
    access_ttl_minutes: int
    pending_ttl_minutes: int


class SmtpSettings(BaseSettings):
    model_config = _get_settings_config_dict("SMTP_")

    host: str
    port: int
    user: str
    password: str
    from_email: str
    use_tls: bool
    use_ssl: bool = False
    timeout: int


class CookieSettings(BaseSettings):
    model_config = _get_settings_config_dict("COOKIE_")

    secure: bool = False
    domain: str | None = None
    samesite: Literal["lax", "strict", "none"] = "lax"


class Settings(BaseSettings):
    model_config = _get_settings_config_dict("")

    database: DatabaseSettings = DatabaseSettings()  # type: ignore[call-arg]
    jwt: JwtSettings = JwtSettings()  # type: ignore[call-arg]
    smtp: SmtpSettings = SmtpSettings()  # type: ignore[call-arg]
    cookie: CookieSettings = CookieSettings()


settings = Settings()
