import os
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated

from sqlmodel import Session
from config import settings
from db import SessionLocal
from deps import require_admin

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/apps")
def get_apps(
    _: Annotated[None, Depends(require_admin)],
) -> list[str]:
    try:
        apps: list[str] = []
        with os.scandir(settings.SIEM_LOG_DIR) as it:
            for entry in it:
                if entry.name.startswith("."):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    apps.append(entry.name)
        apps.sort(key=str.casefold)
        return apps
    except (FileNotFoundError, PermissionError) as e:
        raise HTTPException(status_code=503, detail=f"Log dir not available: {e}")
