from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from fastapi import Request
from sqlmodel import Session, select

from config import settings
from schemas.appState import ReadyAppState
from handlers.exceptions import (
    DatabaseNotReadyError,
    IngestorNotRunningError,
    IngestStateMissingError,
    IngestNotYetPerformedError,
    IngestorStaleError,
)


def get_ready_status(session: Session, request: Request) -> dict[str, Any]:
    app_state = cast(ReadyAppState, request.app.state)

    try:
        _ = session.exec(select(1)).first()
    except Exception as e:
        raise DatabaseNotReadyError(str(e))

    now = datetime.now(timezone.utc)

    ingest_enabled = bool(settings.SIEM_INGEST_ENABLED)

    if not ingest_enabled:
        return {
            "ok": True,
            "db_ok": True,
            "ingest_enabled": False,
            "now": now.isoformat(),
        }

    thread = app_state.ingest_thread
    if thread is None or not thread.is_alive():
        raise IngestorNotRunningError()

    if app_state.ingest_lock is None:
        raise IngestStateMissingError("ingest_lock")
    if app_state.ingest_state is None:
        raise IngestStateMissingError("ingest_state")

    with app_state.ingest_lock:
        st = app_state.ingest_state
        last_ok = st.last_ingest_ok_at
        last_err = st.last_ingest_error
        last_ret_run = st.last_retention_run_at
        last_ret_deleted = st.last_retention_deleted
        last_ret_err = st.last_retention_error

    if last_ok is None:
        raise IngestNotYetPerformedError()

    stale_threshold = max(3 * settings.SIEM_INGEST_POLL_SECONDS, 10)
    age_seconds = (now - last_ok).total_seconds()

    if age_seconds > stale_threshold:
        raise IngestorStaleError(age_seconds, float(stale_threshold))

    return {
        "ok": True,
        "db_ok": True,
        "ingest_enabled": True,
        "ingest_alive": True,
        "now": now.isoformat(),
        "last_ingest_ok_at": last_ok.isoformat(),
        "last_ingest_error": last_err,
        "ingest_age_seconds": age_seconds,
        "stale_threshold_seconds": float(stale_threshold),
        "last_retention_run_at": last_ret_run.isoformat() if last_ret_run else None,
        "last_retention_deleted": last_ret_deleted,
        "last_retention_error": last_ret_err,
    }
