"""tests/unit/test_ranking.py — unit tests for algorithms.ranking
(compute_recency_score, compute_score).
"""

import datetime
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.ranking import compute_recency_score, compute_score


def test_recency_score_at_zero_age_is_100():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    assert compute_recency_score(now, now=now) == 100.0


def test_recency_score_half_life_at_24_hours():
    now = datetime.datetime(2026, 1, 2, 12, 0, 0)
    published = now - datetime.timedelta(hours=24)
    score = compute_recency_score(published, now=now)
    assert math.isclose(score, 50.0, rel_tol=1e-6)


def test_recency_score_future_article_clamped_to_100():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    future = now + datetime.timedelta(hours=5)
    assert compute_recency_score(future, now=now) == 100.0


def test_recency_score_very_old_article_approaches_zero():
    now = datetime.datetime(2026, 1, 30, 0, 0, 0)
    old = now - datetime.timedelta(days=30)
    assert compute_recency_score(old, now=now) < 1.0


def test_compute_score_normal_case_breakdown_matches_final_score():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    article = {"category": "technology", "published_at": now, "popularity_score": 0.8}
    prefs = {"technology": 0.7}
    score, breakdown = compute_score(article, prefs, now=now)

    expected = (
        breakdown["interest"]["contribution"]
        + breakdown["recency"]["contribution"]
        + breakdown["popularity"]["contribution"]
        + breakdown["keyword_relevance"]["contribution"]
        + breakdown["repetition_penalty"]["contribution"]  # already negative
    )
    assert math.isclose(score, expected, rel_tol=1e-9)
    assert math.isclose(score, breakdown["final_score"], rel_tol=1e-9)
    assert breakdown["interest"]["raw"] == 70.0
    assert breakdown["recency"]["raw"] == 100.0
    assert breakdown["popularity"]["raw"] == 80.0


def test_compute_score_unknown_category_uses_cold_start_baseline():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    article = {"category": "unknown_cat", "published_at": now, "popularity_score": 0.0}
    score, breakdown = compute_score(article, user_preferences={}, now=now)
    assert breakdown["interest"]["raw"] == 10.0  # 0.1 baseline * 100


def test_compute_score_with_keyword_relevance_and_penalty():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    article = {"category": "tech", "published_at": now, "popularity_score": 0.0}
    score, breakdown = compute_score(
        article, {"tech": 0.0}, now=now, keyword_relevance=100.0, repetition_penalty=100.0
    )
    assert breakdown["keyword_relevance"]["contribution"] == 15.0
    assert breakdown["repetition_penalty"]["contribution"] == -5.0
