"""backend/api/routes/articles.py — GET /articles, GET /articles/{id},
GET /categories, GET /recommendations/{article_id}.

Routes only parse the request, call a service/repository function, and
serialize the response — no raw SQL, no algorithm logic here.
"""

from typing import Optional

from fastapi import APIRouter, Query

from backend.api.errors import APIError
from backend.api.serializers import serialize_article, serialize_category, serialize_plain_article
from backend.database import repository
from backend.services import recommendation_service

router = APIRouter()

MAX_PAGE_SIZE = 100


@router.get("/categories")
def list_categories() -> list[dict]:
    """GET /categories — list all categories for nav menus."""
    return [serialize_category(c) for c in repository.get_categories()]


@router.get("/articles")
def list_articles(
    page: int = Query(default=1),
    limit: int = Query(default=20),
    category: Optional[int] = Query(default=None),
) -> dict:
    """GET /articles?page,limit,category — browse all articles, paginated.

    400 if page/limit are out of range.
    """
    if page < 1 or limit < 1 or limit > MAX_PAGE_SIZE:
        raise APIError(400, f"page must be >= 1 and limit must be in [1, {MAX_PAGE_SIZE}]", "bad_pagination")

    articles, total = repository.get_articles_paginated(page, limit, category_id=category)
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "articles": [serialize_article(a) for a in articles],
    }


@router.get("/articles/{article_id}")
def get_article(article_id: int) -> dict:
    """GET /articles/{id} — full article detail plus related articles.

    404 if the article doesn't exist.
    """
    article = repository.get_article_by_id(article_id)
    if article is None:
        raise APIError(404, f"Article {article_id} not found", "article_not_found")

    related = recommendation_service.get_related_articles(article_id)
    return {
        "article": serialize_article(article),
        "related": [serialize_plain_article(a) for a in related],
    }


@router.get("/recommendations/{article_id}")
def get_recommendations(article_id: int) -> dict:
    """GET /recommendations/{article_id} — related articles (graph BFS).

    404 if the article doesn't exist (or isn't in the recent candidate window).
    """
    if repository.get_article_by_id(article_id) is None:
        raise APIError(404, f"Article {article_id} not found", "article_not_found")

    related = recommendation_service.get_related_articles(article_id)
    return {"article_id": article_id, "related": [serialize_plain_article(a) for a in related]}
