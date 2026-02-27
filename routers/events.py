from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from db import SessionLocal

from deps import require_admin
from handlers.events import get_event_details
from handlers.exceptions import EventDetailsNotFound
from schemas.apiResponse import EventDetail

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def get_events(_: Annotated[None, Depends(require_admin)]) -> list[str]:
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
