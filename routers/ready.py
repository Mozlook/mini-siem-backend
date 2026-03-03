from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Annotated


from db import SessionLocal
from deps import require_admin
from handlers.exceptions import ReadyCheckError
from handlers.ready import get_ready_status

router = APIRouter(prefix="/ready", tags=["ready"])


@router.get("/")
def get_status(_: Annotated[None, Depends(require_admin)], request: Request):
    with SessionLocal() as session:
        try:
            return get_ready_status(session, request)
        except ReadyCheckError as e:
            raise HTTPException(status_code=503, detail=e.detail)
