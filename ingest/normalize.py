from __future__ import annotations

from datetime import datetime
from pathlib import Path

from config import settings
from models.models import Event
from schemas.incoming import IncomingLogEvent

from .utils import (
    app_from_path,
    cap_text,
    decode_jsonl_line,
    safe_json_dumps,
    utc_now_iso,
    dt_to_utc_rfc3339_z,
)


def build_event(
    incoming: IncomingLogEvent,
    *,
    raw_line: bytes,
    file_path: Path,
    source_file: str,
    source_offset: int,
    received_at: str | None = None,
) -> Event:
    received_at_val = received_at or utc_now_iso()
    ts_dt: datetime | None = incoming.ts
    if ts_dt is None:
        try:
            ts_dt = datetime.fromisoformat(received_at_val.replace("Z", "+00:00"))
        except ValueError:
            ts_dt = None

    ts_str = dt_to_utc_rfc3339_z(ts_dt) if ts_dt is not None else received_at_val

    app = incoming.app or app_from_path(file_path)

    data_json = safe_json_dumps(incoming.data)
    raw_json = decode_jsonl_line(raw_line)

    return Event(
        ts=ts_str,
        received_at=received_at_val,
        app=app,
        host=incoming.host,
        level=incoming.level,
        event_type=incoming.event_type,
        message=cap_text(
            incoming.message,
            settings.SIEM_MAX_MESSAGE_LEN,
            strip=True,
            empty_to_none=True,
        ),
        request_id=incoming.request_id,
        user_id=incoming.user_id,
        src_ip=incoming.src_ip,
        user_agent=cap_text(
            incoming.user_agent,
            settings.SIEM_MAX_USER_AGENT_LEN,
            strip=True,
            empty_to_none=True,
        ),
        http_method=incoming.http_method,
        http_path=cap_text(
            incoming.http_path,
            settings.SIEM_MAX_HTTP_PATH_LEN,
            strip=True,
            empty_to_none=True,
        ),
        http_status=incoming.http_status,
        latency_ms=incoming.latency_ms,
        error_type=incoming.error_type,
        data_json=cap_text(
            data_json,
            settings.SIEM_MAX_DATA_JSON_LEN,
            strip=False,
            empty_to_none=True,
        ),
        raw_json=cap_text(
            raw_json,
            settings.SIEM_MAX_RAW_JSON_LEN,
            strip=False,
            empty_to_none=False,
        ),
        source_file=source_file,
        source_offset=source_offset,
    )
