"""backend/algorithms/ranking.py — the central feed-ranking formula.

    FinalScore =  w1 * InterestScore
                + w2 * RecencyScore
                + w3 * PopularityScore
                + w4 * KeywordRelevance
                - w5 * RepetitionPenalty

All five terms are normalized to 0-100 before weighting, so the weights
(which sum to 1.0 across the four added terms) are directly comparable.
compute_score returns (score, breakdown) from ONE function so the "why am I
seeing this" UI breakdown can never drift out of sync with the actual score.

Pure function: plain dicts in, (float, dict) out, no ORM/framework objects.
"""

import datetime
import math
from typing import Optional

# Default weights (Part 6 of the architecture doc).
WEIGHT_INTEREST = 0.35
WEIGHT_RECENCY = 0.25
WEIGHT_POPULARITY = 0.20
WEIGHT_KEYWORD_RELEVANCE = 0.15
WEIGHT_REPETITION_PENALTY = 0.05

# lambda chosen so a 24h-old article retains ~50% of its recency score:
# 0.5 = e^(-lambda*24)  =>  lambda = ln(2)/24 ~= 0.0289
RECENCY_LAMBDA = math.log(2) / 24


def compute_recency_score(
    published_at: datetime.datetime, now: Optional[datetime.datetime] = None
) -> float:
    """Exponential time-decay recency score, normalized to 0-100.

    Args:
        published_at: when the article was published.
        now: reference time (defaults to current UTC time).

    Returns:
        100 * e^(-lambda * age_hours), clamped to [0, 100]. Future-dated
        articles (age < 0) are clamped to 100 rather than exceeding it.

    Complexity: O(1).
    """
    now = now or datetime.datetime.utcnow()
    age_hours = max(0.0, (now - published_at).total_seconds() / 3600.0)
    return 100.0 * math.exp(-RECENCY_LAMBDA * age_hours)


def compute_score(
    article: dict,
    user_preferences: dict,
    now: Optional[datetime.datetime] = None,
    keyword_relevance: float = 0.0,
    repetition_penalty: float = 0.0,
) -> tuple[float, dict]:
    """Compute an article's final ranking score and its explanation breakdown.

    Args:
        article: dict with at least "category" (hashable key used to look up
            interest) and "published_at" (datetime); "popularity_score"
            (0.0-1.0, default 0) is used for the popularity term.
        user_preferences: {category: weight in [0,1]} — see
            services.preference_engine (Phase 5).
        now: reference time for recency (defaults to current UTC time).
        keyword_relevance: precomputed 0-100 relevance score, only nonzero
            during search (0 otherwise, per the architecture spec).
        repetition_penalty: precomputed 0-100 penalty for showing too much
            of one category/topic already on this page (0 by default; the
            greedy diversification pass does the heavy lifting on this).

    Returns:
        (final_score, breakdown) where breakdown holds each term's raw
        (0-100) value, its weight, and its weighted contribution — exactly
        what the "why am I seeing this" UI panel renders.

    Complexity: O(1) per article.
    """
    category = article.get("category")
    interest_raw = user_preferences.get(category, 0.1) * 100.0
    recency_raw = compute_recency_score(article["published_at"], now)
    popularity_raw = article.get("popularity_score", 0.0) * 100.0

    interest_contribution = WEIGHT_INTEREST * interest_raw
    recency_contribution = WEIGHT_RECENCY * recency_raw
    popularity_contribution = WEIGHT_POPULARITY * popularity_raw
    keyword_contribution = WEIGHT_KEYWORD_RELEVANCE * keyword_relevance
    penalty_contribution = WEIGHT_REPETITION_PENALTY * repetition_penalty

    final_score = (
        interest_contribution
        + recency_contribution
        + popularity_contribution
        + keyword_contribution
        - penalty_contribution
    )

    breakdown = {
        "interest": {"raw": interest_raw, "weight": WEIGHT_INTEREST, "contribution": interest_contribution},
        "recency": {"raw": recency_raw, "weight": WEIGHT_RECENCY, "contribution": recency_contribution},
        "popularity": {"raw": popularity_raw, "weight": WEIGHT_POPULARITY, "contribution": popularity_contribution},
        "keyword_relevance": {"raw": keyword_relevance, "weight": WEIGHT_KEYWORD_RELEVANCE, "contribution": keyword_contribution},
        "repetition_penalty": {"raw": repetition_penalty, "weight": WEIGHT_REPETITION_PENALTY, "contribution": -penalty_contribution},
        "final_score": final_score,
    }

    return final_score, breakdown
