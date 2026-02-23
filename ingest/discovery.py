from pathlib import Path


def discover_jsonl_files(log_dir: str | Path) -> list[Path]:
    base = Path(log_dir)

    if not base.exists():
        return []

    files = [p for p in base.rglob("*.jsonl") if p.is_file()]
    files.sort(key=lambda p: str(p))
    return files
