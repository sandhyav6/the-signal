"""backend/api/routes/trending.py — GET /trending."""

from fastapi import APIRouter, Query

from backend.services import trending_service

router = APIRouter()

DEFAULT_LIMIT = 5


@router.get("/trending")
def get_trending(limit: int = Query(default=DEFAULT_LIMIT)) -> dict:
    """GET /trending?limit — top trending topics with mention counts."""
    topics = trending_service.get_trending_topics(limit=limit)
    return {"topics": [{"topic": topic, "score": score} for topic, score in topics]}
