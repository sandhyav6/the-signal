"""backend/algorithms/trending.py — trending-topics computation.

    TrendingScore(topic) = recent_mentions(topic, window)
                            * recency_factor(avg_age_of_mentions)
                            * engagement_factor(likes+saves+reads)

One pass builds a topic -> (mention_count, total_age_hours, total_engagement)
HashMap in O(n); heap.top_k then selects the top-K topics in O(n log k),
matching the same "why a heap beats a full sort" reasoning as heap.py.

The architecture spec names recency_factor/engagement_factor conceptually
without fixing their exact math (unlike ranking.py's recency half-life,
which is fully specified) — this module picks explicit, documented formulas:
recency_factor reuses ranking.py's exponential decay (consistent with the
rest of the app), and engagement_factor is `1 + log(1 + engagement)` so a
handful of extra likes doesn't let one topic dominate.

Pure function: plain dicts in, list of (topic, score) out.
"""

import datetime
import math
from typing import Optional

from backend.algorithms.heap import top_k
from backend.algorithms.ranking import RECENCY_LAMBDA


def _recency_factor(avg_age_hours: float) -> float:
    """Same exponential decay as ranking.py, scaled to [0, 1]. O(1)."""
    return math.exp(-RECENCY_LAMBDA * max(0.0, avg_age_hours))


def _engagement_factor(engagement: float) -> float:
    """Diminishing-returns engagement multiplier. O(1)."""
    return 1.0 + math.log(1.0 + max(0.0, engagement))


def _build_topic_stats(
    articles: list[dict], cutoff: datetime.datetime, now: datetime.datetime
) -> dict[str, list[float]]:
    """Build a topic -> [mention_count, total_age_hours, total_engagement]
    HashMap over articles published at or after `cutoff`.

    Complexity: O(n) where n = total topic mentions across all articles.
    """
    stats: dict[str, list[float]] = {}
    for article in articles:
        published_at = article["published_at"]
        if published_at < cutoff:
            continue
        age_hours = max(0.0, (now - published_at).total_seconds() / 3600.0)
        engagement = (
            article.get("like_count", 0)
            + article.get("save_count", 0)
            + article.get("read_count", 0)
        )
        for topic in article.get("topics", []):
            entry = stats.setdefault(topic, [0, 0.0, 0.0])
            entry[0] += 1
            entry[1] += age_hours
            entry[2] += engagement
    return stats


def compute_trending(
    articles: list[dict],
    window_hours: float = 24.0,
    top_n: int = 5,
    now: Optional[datetime.datetime] = None,
) -> list[tuple[str, float]]:
    """Compute the top-N trending topics over the last `window_hours`.

    Args:
        articles: dicts with "topics" (list[str]), "published_at" (datetime),
            and optionally "like_count"/"save_count"/"read_count" (each
            default 0, summed as that article's engagement).
        window_hours: only articles published within this many hours of
            `now` are considered.
        top_n: how many top topics to return.
        now: reference time (defaults to current UTC time).

    Returns:
        Up to top_n (topic, trending_score) tuples, sorted descending by
        score. Empty list if no articles fall within the window.

    Complexity: O(n) to build the topic HashMap (n = total topic mentions),
    O(n log top_n) to select the top topics via heap.top_k.
    """
    now = now or datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(hours=window_hours)
    stats = _build_topic_stats(articles, cutoff, now)

    scored: list[tuple[str, float]] = []
    for topic, (count, total_age, total_engagement) in stats.items():
        avg_age = total_age / count
        score = count * _recency_factor(avg_age) * _engagement_factor(total_engagement)
        scored.append((topic, score))

    return top_k(scored, top_n, key=lambda pair: pair[1])
