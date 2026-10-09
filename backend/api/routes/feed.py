"""backend/api/routes/feed.py — GET /feed. Parses the request, calls
feed_service, serializes the response — no ranking/diversification logic
lives here.
"""

from typing import Optional

from fastapi import APIRouter, Query

from backend.api.errors import APIError
from backend.api.serializers import serialize_article, serialize_feed_entry
from backend.database import repository
from backend.services import feed_service

router = APIRouter()

VALID_FEED_TYPES = frozenset({"foryou", "latest", "category"})
PAGE_SIZE = 20
LATEST_WINDOW_DAYS = 7


@router.get("/feed")
def get_feed(
    user_id: int = Query(...),
    type: str = Query(default="foryou"),
    category: Optional[int] = Query(default=None),
    page: int = Query(default=1),
) -> dict:
    """GET /feed?user_id,type=foryou|latest|category,page — the main feed.

    'foryou' is the fully personalized+diversified ranking; 'latest' is a
    plain recency feed (no ranking score to explain); 'category' is the
    personalized ranking restricted to one category.

    400 for an unknown `type` (or `type=category` without a `category`
    param); 404 for an unknown `user_id`.
    """
    if type not in VALID_FEED_TYPES:
        raise APIError(400, f"Unknown feed type: {type!r}", "unknown_feed_type")
    if type == "category" and category is None:
        raise APIError(400, "type=category requires a category query parameter", "missing_category")
    if not repository.user_exists(user_id):
        raise APIError(404, f"User {user_id} not found", "user_not_found")

    if type == "latest":
        recent = repository.get_recent_articles_or_stale(LATEST_WINDOW_DAYS)
        articles = [a for a in recent if a.is_duplicate_of is None][:PAGE_SIZE]
        entries = [{"article": serialize_article(a), "score": None, "breakdown": None} for a in articles]
    else:
        results = feed_service.generate_feed(
            user_id, k=PAGE_SIZE, category_id=category if type == "category" else None
        )
        entries = [serialize_feed_entry(e) for e in results]

    return {"user_id": user_id, "type": type, "page": page, "articles": entries}
