from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from sqlmodel import Session

from config import settings
from db import SessionLocal
from deps import require_admin
from handlers.metadata import get_apps_from_fs, get_event_types_handler
from handlers.exceptions import LogDirUnavailableError

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/apps")
def get_apps(
    _: Annotated[None, Depends(require_admin)],
) -> list[str]:
    try:
        return get_apps_from_fs(settings.SIEM_LOG_DIR)
    except LogDirUnavailableError:
        raise HTTPException(status_code=503, detail="Log dir not available")


@router.get("/event-types")
def get_event_types(
    _: Annotated[None, Depends(require_admin)],
    session: Annotated[Session, Depends(SessionLocal)],
    app: str | None = None,
) -> list[str]:
    return get_event_types_handler(session, app)
