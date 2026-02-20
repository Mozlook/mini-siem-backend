from collections.abc import Sequence
from sqlmodel import Session, select, desc
from models.models import Event


def insert_events_batch(session: Session, events: Sequence[Event]) -> int:
    session.add_all(events)
    return len(events)


def query_latest_events(session: Session, limit: int = 200) -> list[Event]:
    stmt = select(Event).order_by(desc(Event.ts), desc(Event.id)).limit(limit)
    return list(session.exec(stmt).all())
