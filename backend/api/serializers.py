"""backend/api/serializers.py — plain-dict/JSON-safe serializers for API
responses. Keeps ad-hoc field lists out of route files.

Two shapes exist in this codebase and both need serializing here:
  - ORM Article/Category rows (from repository.py's article-by-id,
    paginated-list, bookmarks, history functions).
  - Plain article dicts keyed "category" with a raw datetime (the shape
    feed_service/search_service/recommendation_service already use,
    matching the algorithms/ convention established in Phase 4).
"""

import datetime

from backend.models.models import Article, Category


def serialize_article(article: Article) -> dict:
    """Serialize an ORM Article row into a JSON-safe dict."""
    return {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "url": article.url,
        "image_url": article.image_url,
        "source_name": article.source_name,
        "author": article.author,
        "category_id": article.category_id,
        "published_at": article.published_at.isoformat(),
        "popularity_score": article.popularity_score,
        "like_count": article.like_count,
        "dislike_count": article.dislike_count,
        "save_count": article.save_count,
        "read_count": article.read_count,
    }


def serialize_category(category: Category) -> dict:
    """Serialize an ORM Category row into a JSON-safe dict."""
    return {"id": category.id, "name": category.name, "slug": category.slug}


def serialize_plain_article(article: dict) -> dict:
    """Serialize a plain article dict (feed/search/recommendation_service
    shape: "category" key, raw datetime) into the JSON-safe API shape
    ("category_id" key, ISO date string) used by serialize_article.
    """
    result = dict(article)
    if "category" in result:
        result["category_id"] = result.pop("category")
    published_at = result.get("published_at")
    if isinstance(published_at, datetime.datetime):
        result["published_at"] = published_at.isoformat()
    result.pop("topics", None)
    return result


def serialize_feed_entry(entry: dict) -> dict:
    """Serialize one feed_service.generate_feed() result entry."""
    return {
        "article": serialize_plain_article(entry["article"]),
        "score": entry["score"],
        "breakdown": entry["breakdown"],
    }
