import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone
from config import settings
from ingest.ingest import ingest_loop
from routers import auth, events
from db import init_db

LOG_DIR = Path(settings.SIEM_LOG_DIR)
DB_PATH = Path(settings.SIEM_DB_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from models.models import Event, FileOffset

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    stop_event = threading.Event()
    thread: threading.Thread | None = None

    app.state.ingest_stop_event = stop_event
    app.state.ingest_thread = None

    if settings.SIEM_INGEST_ENABLED:
        thread = threading.Thread(
            target=ingest_loop,
            args=(stop_event,),
            name="mini-siem-ingestor",
            daemon=True,
        )
        thread.start()
        app.state.ingest_thread = thread

    try:
        yield
    finally:
        stop_event.set()
        if thread is not None:
            thread.join(timeout=5)


app = FastAPI(title="Mini-SIEM", version="0.0.1", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.SIEM_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
)

app.include_router(auth.router)
app.include_router(events.router)


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
