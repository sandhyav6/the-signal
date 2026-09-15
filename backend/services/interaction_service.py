"""backend/services/interaction_service.py — orchestrates everything one
user interaction (read/like/save/dislike) triggers: a history record, an
article engagement/popularity bump, and a user_preferences update.

Three separate persistence writes belong together as one unit — this is
exactly what "services orchestrate, repository persists" means, so it does
not live inline in the API route or bundled into repository.py.
"""

import logging
from typing import Optional

from backend.database import repository
from backend.services.preference_engine import INTERACTION_DELTAS, apply_interaction_for_article

logger = logging.getLogger(__name__)

VALID_INTERACTION_TYPES = frozenset(INTERACTION_DELTAS.keys())


def record_interaction(user_id: int, article_id: int, interaction_type: str) -> dict:
    """Record an interaction and apply all of its side effects.

    Args:
        user_id: the acting user.
        article_id: the article interacted with.
        interaction_type: one of 'read', 'like', 'save', 'dislike'.

    Returns:
        {"preference_weight": float | None} — the resulting category weight
        (None if the article has no category, so nothing to personalize).

    Raises:
        ValueError: if interaction_type isn't one of the valid types.

    Complexity: O(1) average (a handful of indexed DB operations).
    """
    if interaction_type not in VALID_INTERACTION_TYPES:
        raise ValueError(f"Unknown interaction_type: {interaction_type!r}")

    repository.record_interaction(user_id, article_id, interaction_type)
    repository.bump_article_engagement(article_id, interaction_type)
    new_weight = apply_interaction_for_article(user_id, article_id, interaction_type)

    return {"preference_weight": new_weight}
