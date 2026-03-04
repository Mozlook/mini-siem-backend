from typing import Any


class LogDirUnavailableError(Exception):
    def __init__(self, log_dir: str, message: str = "Log dir not available"):
        self.log_dir: str = log_dir
        super().__init__(message)


class EventDetailsNotFound(Exception):
    def __init__(self, id: int, message: str = "Event details not found"):
        self.id: int = id
        super().__init__(message)


class ReadyCheckError(Exception):

    def __init__(self, detail: dict[str, Any], message: str = "Service not ready"):
        self.detail = detail
        super().__init__(message)


class DatabaseNotReadyError(ReadyCheckError):
    def __init__(self, error: str):
        super().__init__(
            detail={
                "ok": False,
                "db_ok": False,
                "reason": "db_not_ready",
                "error": error,
            },
            message="Database not ready",
        )


class IngestorNotRunningError(ReadyCheckError):
    def __init__(self):
        super().__init__(
            detail={"ok": False, "db_ok": True, "reason": "ingestor_not_running"},
            message="Ingestor is not running",
        )


class IngestStateMissingError(ReadyCheckError):
    def __init__(self, missing: str):
        super().__init__(
            detail={
                "ok": False,
                "db_ok": True,
                "reason": "ingest_state_missing",
                "missing": missing,
            },
            message="Ingest state missing",
        )


class IngestNotYetPerformedError(ReadyCheckError):
    def __init__(self):
        super().__init__(
            detail={"ok": False, "db_ok": True, "reason": "did_not_ingest_yet"},
            message="No successful ingest yet",
        )


class IngestorStaleError(ReadyCheckError):
    def __init__(self, age_seconds: float, threshold_seconds: float):
        super().__init__(
            detail={
                "ok": False,
                "db_ok": True,
                "reason": "ingestor_stale",
                "ingest_age_seconds": age_seconds,
                "stale_threshold_seconds": threshold_seconds,
            },
            message="Ingestor is stale",
        )


class MetricsUnavailableError(Exception):
    def __init__(self, message: str = "Metrics not available"):
        super().__init__(message)
