from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from config import settings
from deps import require_admin
from handlers.metadata import get_apps_from_fs
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
