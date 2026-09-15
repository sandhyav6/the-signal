"""tests/unit/test_trending.py — unit tests for algorithms.trending.compute_trending."""

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.trending import compute_trending


def _article(topics, hours_ago, now, **engagement):
    return {
        "topics": topics,
        "published_at": now - datetime.timedelta(hours=hours_ago),
        **engagement,
    }


def test_compute_trending_normal_case_ranks_by_mentions():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    articles = [
        _article(["ai"], 1, now),
        _article(["ai"], 2, now),
        _article(["ai"], 3, now),
        _article(["sports"], 1, now),
    ]
    result = compute_trending(articles, window_hours=24, top_n=5, now=now)
    topics = [t for t, _ in result]
    assert topics[0] == "ai"
    assert "sports" in topics


def test_compute_trending_empty_input():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    assert compute_trending([], now=now) == []


def test_compute_trending_excludes_articles_outside_window():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    articles = [_article(["old_topic"], hours_ago=48, now=now)]
    result = compute_trending(articles, window_hours=24, now=now)
    assert result == []


def test_compute_trending_top_n_zero():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    articles = [_article(["ai"], 1, now)]
    assert compute_trending(articles, top_n=0, now=now) == []


def test_compute_trending_top_n_larger_than_topics():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    articles = [_article(["ai"], 1, now), _article(["sports"], 1, now)]
    result = compute_trending(articles, top_n=10, now=now)
    assert len(result) == 2


def test_compute_trending_engagement_increases_score():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    low_engagement = [_article(["topic_a"], 1, now)]
    high_engagement = [_article(["topic_b"], 1, now, like_count=100, save_count=50)]
    low_result = dict(compute_trending(low_engagement, now=now))
    high_result = dict(compute_trending(high_engagement, now=now))
    assert high_result["topic_b"] > low_result["topic_a"]


def test_compute_trending_single_article_single_topic():
    now = datetime.datetime(2026, 1, 1, 12, 0, 0)
    articles = [_article(["solo"], 0, now)]
    result = compute_trending(articles, now=now)
    assert len(result) == 1
    assert result[0][0] == "solo"
