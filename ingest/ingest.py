from datetime import datetime, timezone
from threading import Event
import threading
from time import monotonic
from config import settings
from db import SessionLocal
from ingest.batch import ingest_file_caught_up
from jobs.retention import run_retention_once
from .discovery import discover_jsonl_files
from schemas.ingest import IngestResult, IngestState


def ingest_once(
    log_dir: str, batch_size: int, max_batches_per_file: int
) -> IngestResult:
    paths = discover_jsonl_files(log_dir)
    ingest_result = IngestResult()
    for path in paths:
        try:
            file_path = str(path.resolve())
            file_result = ingest_file_caught_up(
                file_path, batch_size, max_batches_per_file
            )
            ingest_result.files_scanned += 1
            ingest_result.total_inserted += file_result.inserted_count
            ingest_result.total_batches += file_result.batch_count
            ingest_result.stats.non_object += file_result.stats.non_object
            ingest_result.stats.json_errors += file_result.stats.json_errors
            ingest_result.stats.incomplete_lines += file_result.stats.incomplete_lines
            ingest_result.stats.empty_lines += file_result.stats.empty_lines
            ingest_result.stats.validation_errors += file_result.stats.validation_errors
            ingest_result.per_file[file_path] = file_result
        except Exception as e:
            ingest_result.files_failed += 1
            print(e)

    return ingest_result


def ingest_loop(
    stop_event: Event, ingest_lock: threading.Lock, ingest_state: IngestState
) -> None:
    next_retention_due = monotonic() + settings.SIEM_RENENTION_RUN_EVERY_SECONDS
    while not stop_event.is_set():
        try:
            ingest_result = ingest_once(
                settings.SIEM_LOG_DIR,
                settings.SIEM_INGEST_BATCH_SIZE,
                settings.SIEM_INGEST_MAX_BATCHES_PER_FILE,
            )
            with ingest_lock:
                ingest_state.last_ingest_ok_at = datetime.now(timezone.utc)
                ingest_state.last_ingest_error = None
        except Exception as e:
            with ingest_lock:
                ingest_state.last_ingest_error = str(e)

        if settings.SIEM_RENENTION_ENABLED and monotonic() >= next_retention_due:
            with SessionLocal() as session:
                try:
                    deleted = run_retention_once(session, settings.SIEM_RENENTION_DAYS)
                    with ingest_lock:
                        ingest_state.last_retention_run_at = datetime.now(timezone.utc)
                        ingest_state.last_retention_error = None
                        ingest_state.last_retention_deleted = deleted
                except Exception as e:
                    with ingest_lock:
                        ingest_state.last_retention_run_at = datetime.now(timezone.utc)
                        ingest_state.last_retention_error = str(e)
                finally:
                    next_retention_due = (
                        monotonic() + settings.SIEM_RENENTION_RUN_EVERY_SECONDS
                    )

        # print(ingest_result)
        _ = stop_event.wait(timeout=settings.SIEM_INGEST_POLL_SECONDS)
