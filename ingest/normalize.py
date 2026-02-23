from __future__ import annotations

from pathlib import Path

from models.models import Event
from .utils import (
    app_from_path,
    decode_jsonl_line,
    get_float,
    get_int,
    get_text,
    safe_json_dumps,
    utc_now_iso,
)


def build_event_mvp(
    parsed: dict[str, object],
    *,
    raw_line: bytes,
    file_path: Path,
    source_file: str,
    source_offset: int,
    received_at: str | None = None,
) -> Event:
    received_at_val = received_at or utc_now_iso()

    ts = (
        get_text(parsed, "ts")
        or get_text(parsed, "timestamp")
        or get_text(parsed, "time")
        or received_at_val
    )

    app = get_text(parsed, "app") or app_from_path(file_path)

    return Event(
        ts=ts,
        received_at=received_at_val,
        app=app,
        host=get_text(parsed, "host"),
        level=get_text(parsed, "level"),
        event_type=get_text(parsed, "event_type") or get_text(parsed, "type"),
        message=get_text(parsed, "message"),
        request_id=get_text(parsed, "request_id"),
        user_id=get_text(parsed, "user_id"),
        src_ip=get_text(parsed, "src_ip"),
        user_agent=get_text(parsed, "user_agent"),
        http_method=get_text(parsed, "http_method"),
        http_path=get_text(parsed, "http_path"),
        http_status=get_int(parsed, "http_status"),
        latency_ms=get_float(parsed, "latency_ms"),
        error_type=get_text(parsed, "error_type"),
        data_json=safe_json_dumps(parsed.get("data")),
        raw_json=decode_jsonl_line(raw_line),
        source_file=source_file,
        source_offset=source_offset,
    )
