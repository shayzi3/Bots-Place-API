from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_settings_config_dict(env_prefix: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_file=Path(__file__).parent / ".env",
        env_prefix=env_prefix,
        case_sensitive=False,
        extra="ignore",
    )


class Settings(BaseSettings): ...


settings = Settings()
