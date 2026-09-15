"""backend/services/trending_service.py — backs GET /trending. Bridges
algorithms.trending (pure) to the database, so the route never calls the
algorithm directly.
"""

from backend.algorithms.trending import compute_trending
from backend.database import repository

DEFAULT_WINDOW_HOURS = 24.0
CANDIDATE_WINDOW_DAYS = 7


def get_trending_topics(
    limit: int = 5, window_hours: float = DEFAULT_WINDOW_HOURS
) -> list[tuple[str, float]]:
    """Return the top `limit` trending topics over the last `window_hours`.

    Args:
        limit: how many top topics to return.
        window_hours: the trending window (compute_trending filters to
            exactly this; the DB is queried over a wider CANDIDATE_WINDOW_DAYS
            superset first since repository.get_articles_with_topics windows
            in whole days).

    Returns:
        Up to `limit` (topic, trending_score) tuples, sorted descending.

    Complexity: see algorithms.trending.compute_trending.
    """
    articles = repository.get_articles_with_topics(days=CANDIDATE_WINDOW_DAYS)
    return compute_trending(articles, window_hours=window_hours, top_n=limit)
