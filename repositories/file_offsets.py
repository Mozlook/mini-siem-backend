from sqlmodel import Session
from models.models import FileOffset


def get_offset(session: Session, path: str) -> FileOffset | None:
    return session.get(FileOffset, path)


def upsert_offset(
    session: Session, path: str, inode: int, offset: int, updated_at: str
) -> None:
    row = get_offset(session, path)
    if row is None:
        row = FileOffset(path=path, inode=inode, offset=offset, updated_at=updated_at)
        session.add(row)
    else:
        row.inode = inode
        row.offset = offset
        row.updated_at = updated_at
