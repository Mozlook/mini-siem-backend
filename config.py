from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SIEM_ADMIN_PASSWORD_HASH: str
    SIEM_JWT_SECRET: str
    SIEM_CORS_ORIGINS: list[str]
    SIEM_JWT_TTL_SECONDS: int = 604800
    SIEM_JWT_ALG: str = "HS256"
    SIEM_DB_PATH: str = "./data/siem.sqlite3"
    SIEM_LOG_DIR: str = "./sample_logs"

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
