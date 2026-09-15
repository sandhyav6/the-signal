"""backend/api/routes/interactions.py — POST /interactions."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.errors import APIError
from backend.database import repository
from backend.services import interaction_service

router = APIRouter()


class InteractionCreate(BaseModel):
    """POST /interactions request body.

    `type` is the wire/API field name; it is explicitly mapped below to the
    `interaction_type` DB column (see backend/models/models.py
    UserInteraction.interaction_type) — this is the one deliberate place
    the two names differ, and it must stay documented here so it never
    becomes a second silent inconsistency.
    """
    user_id: int
    article_id: int
    type: str


@router.post("/interactions", status_code=201)
def create_interaction(payload: InteractionCreate) -> dict:
    """POST /interactions {user_id,article_id,type} — record an interaction
    (read/like/save/dislike), bump the article's engagement, and update the
    user's category preference weight.

    400 for an invalid `type`; 404 for an unknown user or article.
    """
    if not repository.user_exists(payload.user_id):
        raise APIError(404, f"User {payload.user_id} not found", "user_not_found")
    if repository.get_article_by_id(payload.article_id) is None:
        raise APIError(404, f"Article {payload.article_id} not found", "article_not_found")

    try:
        result = interaction_service.record_interaction(
            user_id=payload.user_id,
            article_id=payload.article_id,
            interaction_type=payload.type,  # JSON "type" -> interaction_type column
        )
    except ValueError as e:
        raise APIError(400, str(e), "invalid_interaction_type") from e

    return {
        "user_id": payload.user_id,
        "article_id": payload.article_id,
        "type": payload.type,
        **result,
    }
