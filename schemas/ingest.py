from sqlmodel import SQLModel, Field

from models.models import Event


class Stats(SQLModel):
    empty_lines: int = 0
    json_errors: int = 0
    non_object: int = 0
    incomplete_lines: int = 0


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
