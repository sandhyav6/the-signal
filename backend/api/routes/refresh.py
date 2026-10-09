"""backend/api/routes/refresh.py — POST /refresh."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.errors import APIError
from backend.services import ingestion

router = APIRouter()

VALID_MODES = frozenset({"mock", "live"})


class RefreshRequest(BaseModel):
    mode: Optional[str] = None


@router.post("/refresh")
def refresh(payload: Optional[RefreshRequest] = None) -> dict:
    """POST /refresh {mode?: 'mock'|'live'} — pull new articles.

    ingestion.ingest() never raises — a live-fetch failure degrades to the
    cached articles (or mock data if nothing is cached), so this endpoint
    always returns 200, never a 500. The response says which `source` was
    actually used and carries a human-readable `message` when it degraded:
    {added, duplicates_skipped, near_duplicates, rejected, source, message}.

    400 for a mode other than 'mock'/'live'.
    """
    mode = payload.mode if payload else None
    if mode is not None and mode not in VALID_MODES:
        raise APIError(400, f"Unknown mode: {mode!r} (expected 'mock' or 'live')", "unknown_mode")
    return ingestion.ingest(mode)
