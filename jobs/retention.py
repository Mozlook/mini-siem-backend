from datetime import timedelta, datetime, timezone
from sqlmodel import Session, col
from sqlalchemy import delete
from ingest.utils import dt_to_utc_rfc3339_z
from models.models import Event


def run_retention_once(session: Session, retention_days: int) -> int:
    now_utc = datetime.now(timezone.utc)
    cutoff_dt = now_utc - timedelta(days=retention_days)
    cutoff_str = dt_to_utc_rfc3339_z(cutoff_dt)

    stmt = delete(Event).where(col(Event.ts) < cutoff_str)
    result = session.exec(stmt)
    session.commit()
    rowcount = result.rowcount or 0
    return rowcount
