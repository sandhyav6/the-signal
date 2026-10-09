"""backend/api/routes/status.py — GET /status."""

from fastapi import APIRouter

from backend.services import ingestion

router = APIRouter()


@router.get("/status")
def get_status() -> dict:
    """GET /status — which data source is in use and whether live news is
    available, so the UI can show a "using sample data" indicator and the
    default mock/live toggle position."""
    return ingestion.get_status()
