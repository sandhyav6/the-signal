"""backend/api/routes/history.py — GET /history."""

from fastapi import APIRouter

from backend.api.errors import APIError
from backend.api.serializers import serialize_article
from backend.database import repository

router = APIRouter()


@router.get("/history")
def get_history(user_id: int) -> dict:
    """GET /history?user_id — articles the user has marked 'read'.

    404 for an unknown user.
    """
    if not repository.user_exists(user_id):
        raise APIError(404, f"User {user_id} not found", "user_not_found")
    articles = repository.get_read_history(user_id)
    return {"user_id": user_id, "articles": [serialize_article(a) for a in articles]}
