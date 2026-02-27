from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import defer
from sqlmodel import Session, select, col

from handlers.exceptions import EventDetailsNotFound
from models.models import Event
from ingest.utils import dt_to_utc_rfc3339_z

MAX_LIMIT = 500


def get_events_all(
    session: Session,
    from_: datetime | None = None,
    to: datetime | None = None,
    app: list[str] | None = None,
    event_type: list[str] | None = None,
    level: list[str] | None = None,
    user_id: str | None = None,
    src_ip: str | None = None,
    request_id: str | None = None,
    http_status: int | None = None,
    q: str | None = None,
    limit: int = 200,
    before_ts: datetime | None = None,
    before_id: int | None = None,
):
    limit = max(1, min(limit, MAX_LIMIT))

    stmt = select(Event).options(defer(Event.raw_json), defer(Event.data_json))

    if from_ is not None:
        from_str = dt_to_utc_rfc3339_z(from_)
        stmt = stmt.where(Event.ts >= from_str)
    if to is not None:
        to_str = dt_to_utc_rfc3339_z(to)
        stmt = stmt.where(Event.ts <= to_str)

    if app:
        stmt = stmt.where(col(Event.app).in_(app))
    if event_type:
        stmt = stmt.where(col(Event.event_type).in_(event_type))
    if level:
        stmt = stmt.where(col(Event.level).in_(level))

    if user_id is not None:
        stmt = stmt.where(Event.user_id == user_id)
    if src_ip is not None:
        stmt = stmt.where(Event.src_ip == src_ip)
    if request_id is not None:
        stmt = stmt.where(Event.request_id == request_id)
    if http_status is not None:
        stmt = stmt.where(Event.http_status == http_status)

    if q is not None:
        stmt = stmt.where(
            or_(col(Event.message).contains(q), col(Event.http_path).contains(q))
        )

    if before_ts is not None or before_id is not None:
        if before_ts is None or before_id is None:
            raise ValueError("before_ts and before_id must be provided together")

        before_ts_str = dt_to_utc_rfc3339_z(before_ts)
        stmt = stmt.where(
            or_(
                col(Event.ts) < before_ts_str,
                and_(col(Event.ts) == before_ts_str, col(Event.id) < before_id),
            )
        )

    stmt = stmt.order_by(col(Event.ts).desc(), col(Event.id).desc()).limit(limit)

    events_list = session.exec(stmt).all()
    return events_list


def get_event_details(id: int, session: Session) -> Event:
    event_details = session.get(Event, id)
    if event_details is None:
        raise EventDetailsNotFound(id)
    return event_details
