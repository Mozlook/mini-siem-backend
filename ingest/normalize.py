import json
from pathlib import Path


from datetime import datetime, timezone


from config import settings


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(d: dict[str, object], key: str) -> str | None:
    v = d.get(key)
    if v is None:
        return None
    if isinstance(v, str):
        return v if v != "" else None
    if isinstance(v, (int, float, bool)):
        return str(v)
    return None


def _int(d: dict[str, object], key: str) -> int | None:
    v = d.get(key)
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


def _float(d: dict[str, object], key: str) -> float | None:
    v = d.get(key)
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _safe_json_dumps(value: object) -> str | None:
    if value is None:
        return None
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return None


def _app_from_path(file_path: Path) -> str | None:

    log_root = Path(settings.SIEM_LOG_DIR).resolve()
    fp = file_path.resolve()
    try:
        rel = fp.relative_to(log_root)
        return rel.parts[0] if rel.parts else None
    except Exception:
        return fp.parent.name or None
