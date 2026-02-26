from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from sqlmodel import Session
from pydantic import ValidationError

from models.models import Event
from repositories.file_offsets import get_offset
from schemas.ingest import Stats, TailResult
from schemas.incoming import IncomingLogEvent

from .normalize import build_event
from .utils import compute_start_offset, utc_now_iso


def read_new_lines_since_last_offset(
    session: Session, path: str | Path, *, max_events: int = 200
) -> TailResult:
    fp = Path(path).resolve()
    path_key = str(fp)
    stats = Stats()
    row = get_offset(session, path_key)
    saved_offset = 0 if row is None or row.offset is None else row.offset
    saved_inode = None if row is None else row.inode

    if not fp.exists():
        return TailResult(events=[], new_offset=saved_offset, inode=None, stats=stats)

    st = fp.stat()
    inode = st.st_ino
    size = st.st_size

    start_offset = compute_start_offset(saved_offset, saved_inode, inode, size)

    events: list[Event] = []
    new_offset = start_offset
    current_line_start_offset = start_offset
    received_at_now = utc_now_iso()

    with fp.open("rb") as f:
        _ = f.seek(start_offset)

        while True:
            if len(events) >= max_events:
                break
            line = f.readline()
            if line == b"":
                break  # EOF

            line_end_offset = f.tell()

            if not line.endswith(b"\n"):
                stats.incomplete_lines += 1
                _ = f.seek(current_line_start_offset)
                break

            if line.strip() == b"":
                stats.empty_lines += 1
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            try:
                parsed_obj: object = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                stats.json_errors += 1
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            if not isinstance(parsed_obj, dict):
                stats.non_object += 1
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            parsed = cast(dict[str, object], parsed_obj)
            try:
                incoming = IncomingLogEvent.model_validate(parsed)

            except ValidationError:
                stats.validation_errors += 1
                new_offset = line_end_offset
                current_line_start_offset = line_end_offset
                continue

            events.append(
                build_event(
                    incoming,
                    raw_line=line,
                    file_path=fp,
                    source_file=path_key,
                    source_offset=current_line_start_offset,
                    received_at=received_at_now,
                )
            )

            new_offset = line_end_offset
            current_line_start_offset = line_end_offset

    return TailResult(events=events, new_offset=new_offset, inode=inode, stats=stats)
