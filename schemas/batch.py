from sqlmodel import SQLModel


class BatchResult(SQLModel):
    inserted_count: int
    new_offset: int
    inode: int | None
    progressed: bool


class FileResult(SQLModel):
    inserted_count: int
    batch_count: int
