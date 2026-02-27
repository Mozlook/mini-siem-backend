from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Annotated

from db import SessionLocal

from deps import require_admin
from handlers.events import get_event_details, get_events_all
from handlers.exceptions import EventDetailsNotFound
from schemas.apiResponse import EventDetail, EventListItem

router = APIRouter(prefix="/events", tags=["events"])

MAX_LIMIT = 500


@router.get("", response_model=list[EventListItem])
def get_events(
    _: Annotated[None, Depends(require_admin)],
    from_: Annotated[datetime | None, Query(alias="from")] = None,
    to: Annotated[datetime | None, Query()] = None,
    app: Annotated[list[str] | None, Query()] = None,
    event_type: Annotated[list[str] | None, Query()] = None,
    level: Annotated[list[str] | None, Query()] = None,
    user_id: Annotated[str | None, Query()] = None,
    src_ip: Annotated[str | None, Query()] = None,
    request_id: Annotated[str | None, Query()] = None,
    http_status: Annotated[int | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 200,
    before_ts: Annotated[datetime | None, Query()] = None,
    before_id: Annotated[int | None, Query(ge=1)] = None,
):
    with SessionLocal() as session:
        try:
            return get_events_all(
                session,
                from_,
                to,
                app,
                event_type,
                level,
                user_id,
                src_ip,
                request_id,
                http_status,
                q,
                limit,
                before_ts,
                before_id,
            )
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="before_ts and before_id must be provided together",
            )


@router.get("/{id}", response_model=EventDetail)
def get_event_by_id(
    _: Annotated[None, Depends(require_admin)],
    id: int,
):
    with SessionLocal() as session:
        try:
            return get_event_details(id, session)
        except EventDetailsNotFound:
            raise HTTPException(status_code=404, detail="Event details not found")
