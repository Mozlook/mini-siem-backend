from __future__ import annotations

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

from models.models import Event


class Stats(SQLModel):
    empty_lines: int = 0
    json_errors: int = 0
    non_object: int = 0
    incomplete_lines: int = 0
    validation_errors: int = 0


class TailResult(SQLModel):
    events: list[Event] = Field(default_factory=list)
    new_offset: int = 0
    inode: int | None = None
    stats: Stats = Field(default_factory=Stats)


class BatchResult(SQLModel):
    inserted_count: int = 0
    new_offset: int = 0
    inode: int | None = None
    progressed: bool = False
    stats: Stats = Field(default_factory=Stats)


class FileResult(SQLModel):
    inserted_count: int = 0
    batch_count: int = 0
    stats: Stats = Field(default_factory=Stats)


class IngestResult(SQLModel):
    files_scanned: int = 0
    files_failed: int = 0
    total_inserted: int = 0
    total_batches: int = 0
    stats: Stats = Field(default_factory=Stats)
    per_file: dict[str, FileResult] = Field(default_factory=dict)


class IngestMetrics(SQLModel):
    files_scanned: int = 0
    files_failed: int = 0
    total_inserted: int = 0
    total_batches: int = 0
    stats: Stats = Field(default_factory=Stats)

    @classmethod
    def from_ingest_result(cls, r: IngestResult) -> IngestMetrics:
        return cls(
            files_scanned=r.files_scanned,
            files_failed=r.files_failed,
            total_inserted=r.total_inserted,
            total_batches=r.total_batches,
            stats=Stats(**r.stats.model_dump()),
        )


class IngestState(SQLModel):
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    metrics_total: IngestMetrics = Field(default_factory=IngestMetrics)
    metrics_last: IngestMetrics = Field(default_factory=IngestMetrics)

    last_ingest_ok_at: datetime | None = None
    last_ingest_error: str | None = None

    last_retention_run_at: datetime | None = None
    last_retention_deleted: int = 0
    last_retention_error: str | None = None
