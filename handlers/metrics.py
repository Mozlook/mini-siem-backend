from __future__ import annotations

from typing import cast

from fastapi import Request

from handlers.exceptions import MetricsUnavailableError
from schemas.appState import MetricsAppState
from schemas.ingest import (
    IngestState,
)


def get_metrics_handler(request: Request) -> IngestState:
    raw_state = request.app.state

    if not hasattr(raw_state, "ingest_lock") or not hasattr(raw_state, "ingest_state"):
        raise MetricsUnavailableError(
            "missing ingest_lock or ingest_state on app.state"
        )

    app_state = cast(MetricsAppState, raw_state)

    with app_state.ingest_lock:
        return app_state.ingest_state.model_copy(deep=True)
