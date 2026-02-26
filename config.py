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
    SIEM_INGEST_ENABLED: bool = True
    SIEM_INGEST_POLL_SECONDS: int = 2
    SIEM_INGEST_BATCH_SIZE: int = 200
    SIEM_INGEST_MAX_BATCHES_PER_FILE: int = 50
    SIEM_MAX_MESSAGE_LEN: int = 5000
    SIEM_MAX_USER_AGENT_LEN: int = 2000
    SIEM_MAX_HTTP_PATH_LEN: int = 2000
    SIEM_MAX_RAW_JSON_LEN: int = 200000
    SIEM_MAX_DATA_JSON_LEN: int = 50000

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8"
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
