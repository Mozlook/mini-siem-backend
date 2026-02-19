from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
import os

LOG_DIR = Path(os.getenv("SIEM_LOG_DIR", "/logs"))
DB_PATH = Path(os.getenv("SIEM_DB_PATH", "/data/siem.sqlite3"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.touch(exist_ok=True)
    yield


app = FastAPI(title="Mini-SIEM", version="0.0.1", lifespan=lifespan)


@app.get("/health")
def health():
    now = datetime.now(timezone.utc).isoformat()

    logs_exists = LOG_DIR.exists()
    jsonl_files = []
    if logs_exists:
        jsonl_files = [str(p) for p in LOG_DIR.rglob("*.jsonl")][:50]

    return {
        "status": "ok",
        "ts_utc": now,
        "log_dir": str(LOG_DIR),
        "log_dir_exists": logs_exists,
        "sample_jsonl_files": jsonl_files,
        "db_path": str(DB_PATH),
        "db_file_exists": DB_PATH.exists(),
    }
