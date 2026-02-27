from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from db import SessionLocal

from deps import require_admin
from handlers.events import get_event_details
from handlers.exceptions import EventDetailsNotFound
from schemas.apiResponse import EventDetail, EventListItem

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventListItem])
def get_events(
    _: Annotated[None, Depends(require_admin)],
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
    return []


@router.get("{id}", response_model=EventDetail)
def get_event_by_id(
    _: Annotated[None, Depends(require_admin)],
    id: int,
):
    with SessionLocal() as session:
        try:
            return get_event_details(id, session)
        except EventDetailsNotFound:
            raise HTTPException(status_code=404, detail="Event details not found")
