from fastapi import APIRouter, Depends
from typing import Annotated
from deps import require_admin

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def get_events(_: Annotated[None, Depends(require_admin)]) -> list[str]:
    return []
