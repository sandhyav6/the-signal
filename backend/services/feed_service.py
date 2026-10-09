"""backend/services/feed_service.py — the main feed-generation pipeline.

    recent candidates -> per-article scoring (ranking.compute_score)
                       -> heap Top-K (heap.top_k)
                       -> greedy diversification (diversification.greedy_diversify)

This is what backs `GET /feed` once the API layer exists (Phase 6). It
bridges ORM Article rows into the plain dicts the pure algorithms/ modules
require, and back.
"""

import datetime
from typing import Optional

from backend.algorithms.diversification import greedy_diversify
from backend.algorithms.heap import top_k
from backend.algorithms.ranking import compute_score
from backend.database import repository
from backend.models.models import Article

DEFAULT_RECENT_DAYS = 7
DEFAULT_TOP_K = 20
DEFAULT_MAX_PER_CATEGORY = 3


def _article_to_dict(article: Article) -> dict:
    """Convert an ORM Article row into the plain dict algorithms/ expects.

    Only plain columns are read (never relationships), so this is safe to
    call after the row's session has closed.

    Complexity: O(1).
    """
    return {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "url": article.url,
        "image_url": article.image_url,
        "source_name": article.source_name,
        "category": article.category_id,
        "published_at": article.published_at,
        "popularity_score": article.popularity_score,
    }


def generate_feed(
    user_id: int,
    k: int = DEFAULT_TOP_K,
    max_per_category: int = DEFAULT_MAX_PER_CATEGORY,
    recent_days: int = DEFAULT_RECENT_DAYS,
    now: Optional[datetime.datetime] = None,
    category_id: Optional[int] = None,
) -> list[dict]:
    """Generate a ranked, diversified, explained feed for one user.

    Args:
        user_id: whose preferences to rank against.
        k: how many articles the ranked feed should contain before
            diversification (diversification only re-orders/defers, it
            never adds articles beyond this set).
        max_per_category: diversification cap per category per page.
        recent_days: candidate window — only articles published in the last
            `recent_days` days are considered.
        now: reference time (defaults to current UTC time); threaded through
            to recency scoring so tests can pin "now" deterministically.
        category_id: if given, restrict candidates to this category only
            (backs GET /feed?type=category).

    Returns:
        A list of up to k dicts, each: {"article": <plain article dict>,
        "score": float, "breakdown": dict}, ranked and diversified. Articles
        marked as a duplicate of another (is_duplicate_of set) are excluded.

    Complexity: O(n) to load/score candidates, O(n log k) for Top-K
    selection, O(k) for the greedy diversification pass.

    If nothing was published in the last `recent_days` days (stale cached
    or sample data), the window widens rather than returning an empty
    feed — recency then contributes ~0 and the other terms decide order.
    """
    now = now or datetime.datetime.utcnow()

    articles = repository.get_recent_articles_or_stale(recent_days)
    candidates = [_article_to_dict(a) for a in articles if a.is_duplicate_of is None]
    if category_id is not None:
        candidates = [c for c in candidates if c["category"] == category_id]

    preferences = repository.get_user_category_preferences(user_id)

    scored = []
    for candidate in candidates:
        score, breakdown = compute_score(candidate, preferences, now=now)
        scored.append({"article": candidate, "score": score, "breakdown": breakdown})

    ranked = top_k(scored, k, key=lambda entry: entry["score"])
    return greedy_diversify(
        ranked, max_per_category, category_key=lambda entry: entry["article"]["category"]
    )
