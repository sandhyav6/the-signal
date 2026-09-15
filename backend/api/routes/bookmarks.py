"""backend/api/routes/bookmarks.py — POST /bookmarks, GET /bookmarks."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.errors import APIError
from backend.api.serializers import serialize_article
from backend.database import repository

router = APIRouter()


class BookmarkCreate(BaseModel):
    user_id: int
    article_id: int


@router.post("/bookmarks", status_code=201)
def create_bookmark(payload: BookmarkCreate) -> dict:
    """POST /bookmarks {user_id,article_id} — save an article.

    404 for an unknown user or article.
    """
    if not repository.user_exists(payload.user_id):
        raise APIError(404, f"User {payload.user_id} not found", "user_not_found")
    if repository.get_article_by_id(payload.article_id) is None:
        raise APIError(404, f"Article {payload.article_id} not found", "article_not_found")

    created = repository.add_bookmark(payload.user_id, payload.article_id)
    return {"user_id": payload.user_id, "article_id": payload.article_id, "created": created}


@router.get("/bookmarks")
def list_bookmarks(user_id: int) -> dict:
    """GET /bookmarks?user_id — a user's saved articles.

    404 for an unknown user.
    """
    if not repository.user_exists(user_id):
        raise APIError(404, f"User {user_id} not found", "user_not_found")
    articles = repository.get_bookmarked_articles(user_id)
    return {"user_id": user_id, "articles": [serialize_article(a) for a in articles]}
