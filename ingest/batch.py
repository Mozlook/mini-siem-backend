from datetime import datetime, timezone
from pathlib import Path
from schemas.ingest import BatchResult, FileResult, Stats
from db import SessionLocal
from repositories.events import insert_events_batch
from repositories.file_offsets import upsert_offset, get_offset
from .tail import read_new_lines_since_last_offset


def ingest_one_batch_for_file(path: str, batch_size: int) -> BatchResult:
    path_key = str(Path(path).resolve())
    session = SessionLocal()
    prev_offset = 0
    prev_inode: int | None = None
    stats = Stats()
    try:
        row = get_offset(session, path_key)
        if row:
            prev_offset = row.offset or 0
            prev_inode = row.inode
        tail_result = read_new_lines_since_last_offset(
            session, path_key, max_events=batch_size
        )
        events = tail_result.events
        offset = tail_result.new_offset
        inode = tail_result.inode
        stats = tail_result.stats

        if inode is None:
            session.close()
            return BatchResult(
                inserted_count=0, new_offset=0, inode=0, progressed=False, stats=stats
            )
        inserted_count = len(events)
        if inserted_count > 0:
            _ = insert_events_batch(session, events)

        now_iso_utc = (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )
        progressed = (row is None) or (offset != prev_offset) or (inode != prev_inode)

        if progressed:
            upsert_offset(session, path_key, inode, offset, now_iso_utc)

        if progressed or inserted_count != 0:
            session.commit()

        session.close()
        return BatchResult(
            inserted_count=inserted_count,
            new_offset=offset,
            inode=inode,
            progressed=progressed,
            stats=stats,
        )
    except Exception as e:
        print(e)
        session.rollback()
        session.close()
        return BatchResult(
            inserted_count=0,
            new_offset=prev_offset,
            inode=prev_inode,
            progressed=False,
            stats=stats,
        )


def ingest_file_caught_up(
    path: str, batch_size: int, max_batches_per_file: int
) -> FileResult:
    file_result = FileResult(inserted_count=0, batch_count=0, stats=Stats())
    remaining = max_batches_per_file
    while True:
        remaining -= 1
        batch_result = ingest_one_batch_for_file(path, batch_size)
        file_result.inserted_count += batch_result.inserted_count
        file_result.batch_count += 1
        file_result.stats.non_object += batch_result.stats.non_object
        file_result.stats.json_errors += batch_result.stats.json_errors
        file_result.stats.incomplete_lines += batch_result.stats.incomplete_lines
        file_result.stats.empty_lines += batch_result.stats.empty_lines
        if (
            not batch_result.progressed
            or batch_result.inserted_count < batch_size
            or remaining <= 0
        ):
            return file_result
