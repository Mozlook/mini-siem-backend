from threading import Thread
from typing import Protocol
from schemas.ingest import IngestState
from _thread import LockType


class ReadyAppState(Protocol):
    ingest_thread: Thread | None
    ingest_lock: LockType | None
    ingest_state: IngestState | None


class MetricsAppState(Protocol):
    ingest_lock: LockType
    ingest_state: IngestState
