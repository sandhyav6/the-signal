"""backend/api/routes/refresh.py — POST /refresh."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services import ingestion

router = APIRouter()


class RefreshRequest(BaseModel):
    mode: Optional[str] = None


@router.post("/refresh")
def refresh(payload: Optional[RefreshRequest] = None) -> dict:
    """POST /refresh {mode?: 'mock'|'live'} — pull new articles.

    ingestion.ingest() never raises — a live-fetch failure is caught inside
    it and falls back to mock data, so this endpoint always returns 200
    with the resulting {added, duplicates_skipped} counts, never a 500.
    """
    mode = payload.mode if payload else None
    return ingestion.ingest(mode)
