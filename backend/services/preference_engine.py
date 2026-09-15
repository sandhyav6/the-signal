"""backend/services/preference_engine.py — updates a user's per-category
preference weight in response to an interaction.

    read    -> +0.03   (>10s dwell, or explicit "mark read")
    like    -> +0.10
    save    -> +0.15   (bookmark)
    dislike -> -0.15   ("not interested")

Deterministic and transparent — a simple clamped additive rule, no ML. This
is the "loop" in the architecture's dynamic-behavior diagram: an interaction
here changes `user_preferences`, and the *next* feed_service.generate_feed()
call re-scores against the new weight.
"""

import logging
from typing import Optional

from backend.database import repository

logger = logging.getLogger(__name__)

INTERACTION_DELTAS = {
    "read": 0.03,
    "like": 0.10,
    "save": 0.15,
    "dislike": -0.15,
}

MIN_WEIGHT = 0.0
MAX_WEIGHT = 1.0


def compute_new_weight(current_weight: float, interaction_type: str) -> float:
    """Apply one interaction's preference delta, clamped to [0, 1].

    Args:
        current_weight: the category's current preference weight.
        interaction_type: one of 'read', 'like', 'save', 'dislike'.

    Returns:
        The new weight, clamped to [MIN_WEIGHT, MAX_WEIGHT].

    Raises:
        ValueError: if interaction_type isn't a recognized type.

    Complexity: O(1).
    """
    if interaction_type not in INTERACTION_DELTAS:
        raise ValueError(f"Unknown interaction_type: {interaction_type!r}")
    delta = INTERACTION_DELTAS[interaction_type]
    return max(MIN_WEIGHT, min(MAX_WEIGHT, current_weight + delta))


def apply_interaction(user_id: int, category_id: int, interaction_type: str) -> float:
    """Update a user's preference weight for a category after an interaction.

    Args:
        user_id: the acting user.
        category_id: the category to adjust (typically the interacted
            article's category).
        interaction_type: one of 'read', 'like', 'save', 'dislike'.

    Returns:
        The resulting (clamped) weight, already persisted.

    Complexity: O(1) average (two indexed DB lookups/writes).
    """
    current = repository.get_user_category_weight(user_id, category_id)
    new_weight = compute_new_weight(current, interaction_type)
    repository.set_user_category_weight(user_id, category_id, new_weight)
    logger.info(
        "[preference_engine.apply_interaction] user=%s category=%s type=%s %.3f -> %.3f",
        user_id, category_id, interaction_type, current, new_weight,
    )
    return new_weight


def apply_interaction_for_article(
    user_id: int, article_id: int, interaction_type: str
) -> Optional[float]:
    """Convenience wrapper: resolve an article's category, then apply_interaction.

    Args:
        user_id: the acting user.
        article_id: the article the user interacted with.
        interaction_type: one of 'read', 'like', 'save', 'dislike'.

    Returns:
        The resulting weight, or None if the article has no category (or
        doesn't exist) — nothing to update in that case.

    Complexity: O(1) average.
    """
    category_id = repository.get_article_category(article_id)
    if category_id is None:
        logger.warning(
            "[preference_engine.apply_interaction_for_article] article=%s has no category; skipping preference update",
            article_id,
        )
        return None
    return apply_interaction(user_id, category_id, interaction_type)
