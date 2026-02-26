import json
from datetime import datetime, timezone
from pathlib import Path

from config import settings


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compute_start_offset(
    saved_offset: int,
    saved_inode: int | None,
    inode: int,
    size: int,
) -> int:
    if saved_inode is not None and saved_inode != inode:
        return 0
    if saved_offset > size:
        return 0
    return saved_offset


def app_from_path(file_path: Path) -> str | None:
    log_root = Path(settings.SIEM_LOG_DIR).resolve()
    fp = file_path.resolve()
    try:
        rel = fp.relative_to(log_root)
        return rel.parts[0] if rel.parts else None
    except Exception:
        return fp.parent.name or None


def decode_jsonl_line(line: bytes) -> str:
    return line.decode("utf-8", errors="replace").rstrip("\r\n")


def safe_json_dumps(value: object) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return None


def cap_text(
    value: str | None,
    max_len: int,
    *,
    strip: bool = False,
    empty_to_none: bool = False,
) -> str | None:
    if value is None:
        return None

    if strip:
        value = value.strip()

    if empty_to_none and value == "":
        return None

    if max_len <= 0:
        return value

    if len(value) <= max_len:
        return value

    return value[:max_len]


def dt_to_utc_rfc3339_z(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    s = dt.isoformat(timespec="microseconds")
    if s.endswith("+00:00"):
        s = s[:-6] + "Z"
    return s
