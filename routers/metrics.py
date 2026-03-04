from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from deps import require_admin
from handlers.exceptions import MetricsUnavailableError
from handlers.metrics import get_metrics_handler
from schemas.ingest import IngestState

router = APIRouter(prefix="/metrics", tags=["ops"])


@router.get("/", response_model=IngestState)
def get_metrics(
    _: Annotated[None, Depends(require_admin)],
    request: Request,
) -> IngestState:
    try:
        return get_metrics_handler(request)
    except MetricsUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
