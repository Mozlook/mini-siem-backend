import json
from datetime import datetime, timezone
from pathlib import Path
from posix import truncate

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


def get_text(d: dict[str, object], key: str) -> str | None:
    v = d.get(key)
    if v is None:
        return None
    if isinstance(v, str):
        return v if v != "" else None
    if isinstance(v, (int, float, bool)):
        return str(v)
    return None


def get_int(d: dict[str, object], key: str) -> int | None:
    v = d.get(key)
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def get_float(d: dict[str, object], key: str) -> float | None:
    v = d.get(key)
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def cap_text(value: str | None, max_len: int) -> str | None:
    if value is None:
        return None
    if max_len <= 0:
        return value
    if len(value) <= max_len:
        return value
    return value[:max_len]
