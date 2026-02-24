from sqlmodel import SQLModel

from models.models import Event


class Stats(SQLModel):
    empty_lines: int = 0
    json_errors: int = 0
    non_object: int = 0
    incomplete_lines: int = 0


class TailResult(SQLModel):
    events: list[Event]
    new_offset: int
    inode: int | None
    stats: Stats


class BatchResult(SQLModel):
    inserted_count: int
    new_offset: int
    inode: int | None
    progressed: bool
    stats: Stats


class FileResult(SQLModel):
    inserted_count: int
    batch_count: int
    stats: Stats
