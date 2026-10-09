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

    If no topic was mentioned inside the window, falls back to ranking
    every stored article rather than returning nothing.

    Complexity: see algorithms.trending.compute_trending (run at most twice).
    """
    articles = repository.get_articles_with_topics(days=CANDIDATE_WINDOW_DAYS)
    trending = compute_trending(articles, window_hours=window_hours, top_n=limit)
    if trending:
        return trending
    # Nothing in the window (stale cache / sample data): rank over everything
    # stored, so the rail still shows the most-covered topics.
    stale_hours = repository.STALE_FALLBACK_DAYS * 24.0
    articles = repository.get_articles_with_topics(days=repository.STALE_FALLBACK_DAYS)
    return compute_trending(articles, window_hours=stale_hours, top_n=limit)
