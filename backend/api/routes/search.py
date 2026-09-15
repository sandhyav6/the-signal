"""backend/api/routes/search.py — GET /search, GET /search/suggest."""

from fastapi import APIRouter, Query

from backend.api.errors import APIError
from backend.api.serializers import serialize_plain_article
from backend.services import search_service

router = APIRouter()

PAGE_SIZE = 20
SUGGEST_LIMIT = 10


@router.get("/search")
def search(q: str = Query(default=""), page: int = Query(default=1)) -> dict:
    """GET /search?q,page — substring search over titles/descriptions.

    400 if `q` is empty.
    """
    if not q.strip():
        raise APIError(400, "Query parameter 'q' must not be empty", "empty_query")

    results, total = search_service.search_articles(q, page=page, limit=PAGE_SIZE)
    return {
        "query": q,
        "page": page,
        "total": total,
        "articles": [serialize_plain_article(a) for a in results],
    }


@router.get("/search/suggest")
def suggest(prefix: str = Query(default="")) -> dict:
    """GET /search/suggest?prefix — Trie-backed autocomplete."""
    return {"prefix": prefix, "suggestions": search_service.suggest(prefix, limit=SUGGEST_LIMIT)}
