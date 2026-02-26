from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class IncomingLogEvent(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    ts: datetime | None = Field(
        default=None,
        validation_alias=AliasChoices("ts", "timestamp", "time"),
    )
    app: str | None = None
    host: str | None = None
    level: str | None = None

    event_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("event_type", "type"),
    )
    message: str | None = Field(
        default=None,
        validation_alias=AliasChoices("msg", "message"),
    )

    request_id: str | None = None
    user_id: str | None = None
    src_ip: str | None = None
    user_agent: str | None = None

    http_status: int | None = Field(
        default=None,
        validation_alias=AliasChoices("status", "http_status"),
    )
    http_method: str | None = Field(
        default=None,
        validation_alias=AliasChoices("method", "http_method"),
    )
    http_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("path", "http_path"),
    )
    latency_ms: float | None = None

    error_type: str | None = None

    data: Any | None = None

    @field_validator("ts")
    @classmethod
    def _ts_to_utc(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)

    @field_validator("http_status", mode="before")
    @classmethod
    def _soft_int(cls, v: Any) -> int | None:
        if v is None or v == "":
            return None
        if isinstance(v, bool):  # avoid True -> 1
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    @field_validator("latency_ms", mode="before")
    @classmethod
    def _soft_float(cls, v: Any) -> float | None:
        if v is None or v == "":
            return None
        if isinstance(v, bool):
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @field_validator(
        "app",
        "host",
        "level",
        "event_type",
        "message",
        "request_id",
        "user_id",
        "src_ip",
        "user_agent",
        "http_method",
        "http_path",
        "error_type",
        mode="before",
    )
    @classmethod
    def _text_normalize(cls, v: Any) -> str | None:
        """
        Normalize text-ish fields:
        - numbers/bools -> str
        - empty/whitespace -> None
        - non-primitive objects -> None
        """
        if v is None:
            return None
        if isinstance(v, (int, float, bool)):
            v = str(v)
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return None
