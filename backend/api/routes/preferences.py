"""backend/api/routes/preferences.py — GET /preferences, PUT /preferences."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.errors import APIError
from backend.database import repository

router = APIRouter()


class PreferencesUpdate(BaseModel):
    """PUT /preferences body. `updates` keys are category ids (JSON object
    keys are always strings, so they're parsed to int below) mapped to the
    new weight for that category.
    """
    user_id: int
    updates: dict[str, float]


@router.get("/preferences")
def get_preferences(user_id: int) -> dict:
    """GET /preferences?user_id — a user's category preference map.

    404 for an unknown user.
    """
    if not repository.user_exists(user_id):
        raise APIError(404, f"User {user_id} not found", "user_not_found")
    return {"user_id": user_id, "preferences": repository.get_user_category_preferences(user_id)}


@router.put("/preferences")
def update_preferences(payload: PreferencesUpdate) -> dict:
    """PUT /preferences {user_id, updates:{category_id: weight}} — manual
    interest editing (as opposed to preference_engine's interaction-driven
    deltas).

    400 if any weight is outside [0,1] or any category id is unknown/not an
    integer; 404 if the user doesn't exist.
    """
    if not repository.user_exists(payload.user_id):
        raise APIError(404, f"User {payload.user_id} not found", "user_not_found")

    known_categories = {c.id for c in repository.get_categories()}
    parsed_updates: dict[int, float] = {}
    for raw_category_id, weight in payload.updates.items():
        try:
            category_id = int(raw_category_id)
        except ValueError as e:
            raise APIError(400, f"Invalid category id: {raw_category_id!r}", "invalid_category") from e
        if category_id not in known_categories:
            raise APIError(400, f"Unknown category id: {category_id}", "invalid_category")
        if not (0.0 <= weight <= 1.0):
            raise APIError(400, f"Weight for category {category_id} must be in [0,1], got {weight}", "invalid_weight")
        parsed_updates[category_id] = weight

    updated = repository.set_user_preferences_bulk(payload.user_id, parsed_updates)
    return {"user_id": payload.user_id, "preferences": updated}
