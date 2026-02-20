from sqlmodel import SQLModel


class FileOffsetBase(SQLModel):
    inode: int | None = None
    offset: int | None = None
    updated_at: str | None = None
