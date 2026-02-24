from sqlmodel import SQLModel


class BatchResult(SQLModel):
    inserted_count: int
    new_offset: int
    inode: int | None
    progressed: bool
