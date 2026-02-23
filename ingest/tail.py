import json
from sqlmodel import Session
from pathlib import Path

from models.models import Event
from repositories.file_offsets import get_offset

from typing import cast

from .normalize import (
    _utc_now_iso,
    _app_from_path,
    _float,
    _int,
    _safe_json_dumps,
    _text,
)


def read_new_lines_since_last_offset(
    session: Session, path: str | Path
) -> tuple[list[Event], int, int | None]:
    fp = Path(path).resolve()
    path_key = str(fp)

    row = get_offset(session, path_key)
    start_offset = 0 if row is None or row.offset is None else row.offset

    saved_offset = 0 if row is None or row.offset is None else row.offset
    saved_inode = 0 if row is None else row.inode

    if not fp.exists():
        return [], start_offset, None

    stat_result = fp.stat()
    inode = stat_result.st_ino
    size = stat_result.st_size

    if saved_inode != inode:
        start_offset = 0
    elif saved_offset > size:
        start_offset = 0
    else:
        start_offset = saved_offset

    events: list[Event] = []
    new_offset = start_offset
    current_line_start_offset = start_offset

    received_at_now = _utc_now_iso()

    with fp.open("rb") as f:
        _ = f.seek(start_offset)

        while True:
            line = f.readline()
            if line == b"":
                # EOF
                break

            line_end_offset = f.tell()

            if not line.endswith(b"\n"):
                _ = f.seek(current_line_start_offset)
                break

            if line.strip() == b"":
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            if not isinstance(parsed, dict):
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            obj = cast(dict[str, object], parsed)

            ts = (
                _text(obj, "ts")
                or _text(obj, "timestamp")
                or _text(obj, "time")
                or received_at_now
            )
            app = _text(obj, "app") or _app_from_path(fp)

            raw_json_str = line.decode("utf-8", errors="replace").rstrip("\r\n")

            event = Event(
                ts=ts,
                received_at=received_at_now,
                app=app,
                host=_text(obj, "host"),
                level=_text(obj, "level"),
                event_type=_text(obj, "event_type") or _text(obj, "type"),
                message=_text(obj, "message"),
                request_id=_text(obj, "request_id"),
                user_id=_text(obj, "user_id"),
                src_ip=_text(obj, "src_ip"),
                user_agent=_text(obj, "user_agent"),
                http_method=_text(obj, "http_method"),
                http_path=_text(obj, "http_path"),
                http_status=_int(obj, "http_status"),
                latency_ms=_float(obj, "latency_ms"),
                error_type=_text(obj, "error_type"),
                data_json=_safe_json_dumps(obj.get("data")),
                raw_json=raw_json_str,
                source_file=path_key,
                source_offset=current_line_start_offset,
            )

            events.append(event)

            new_offset = line_end_offset
            current_line_start_offset = line_end_offset

    return events, new_offset, inode
