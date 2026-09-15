"""tests/integration/test_api_to_algorithm.py — route-level tests proving
each algorithm-backed endpoint is correctly wired end-to-end (HTTP request
-> service -> algorithms/ -> HTTP response), not just that the underlying
algorithm functions work in isolation (already covered by tests/unit/).
"""

import datetime

from tests.integration.conftest import (
    SPORTS_CATEGORY_ID,
    TECH_CATEGORY_ID,
    seed_article,
    seed_categories,
    seed_user,
)

NOW = datetime.datetime.utcnow()


def test_feed_ranks_by_preference_and_diversifies(client, fresh_db):
    """GET /feed?type=foryou must be wired through ranking + heap + diversification."""
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session, with_preferences=False)
        from backend.models.models import UserPreference
        session.add(UserPreference(user_id=1, category_id=TECH_CATEGORY_ID, topic_id=None, weight=0.9))
        session.add(UserPreference(user_id=1, category_id=SPORTS_CATEGORY_ID, topic_id=None, weight=0.1))
        for i in range(1, 4):
            seed_article(session, i, f"Tech {i}", category_id=TECH_CATEGORY_ID, published_at=NOW)
        for i in range(4, 7):
            seed_article(session, i, f"Sports {i}", category_id=SPORTS_CATEGORY_ID, published_at=NOW)
        session.commit()

    resp = client.get("/feed?user_id=1&type=foryou")
    assert resp.status_code == 200
    body = resp.json()
    categories = [e["article"]["category_id"] for e in body["articles"]]
    assert categories[0] == TECH_CATEGORY_ID
    assert all("final_score" in e["breakdown"] for e in body["articles"])


def test_feed_type_category_filters_to_one_category(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        seed_article(session, 1, "Tech Story", category_id=TECH_CATEGORY_ID, published_at=NOW)
        seed_article(session, 2, "Sports Story", category_id=SPORTS_CATEGORY_ID, published_at=NOW)
        session.commit()

    resp = client.get(f"/feed?user_id=1&type=category&category={SPORTS_CATEGORY_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["articles"]) == 1
    assert body["articles"][0]["article"]["category_id"] == SPORTS_CATEGORY_ID


def test_feed_unknown_type_returns_400(client, fresh_db):
    with fresh_db() as session:
        seed_user(session, with_preferences=False)
        session.commit()
    resp = client.get("/feed?user_id=1&type=bogus")
    assert resp.status_code == 400
    assert resp.json()["code"] == "unknown_feed_type"


def test_feed_unknown_user_returns_404(client, fresh_db):
    resp = client.get("/feed?user_id=999")
    assert resp.status_code == 404
    assert resp.json()["code"] == "user_not_found"


def test_search_finds_substring_match(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "OpenAI Releases GPT-5", category_id=TECH_CATEGORY_ID, published_at=NOW)
        seed_article(session, 2, "Cricket World Cup Final", category_id=SPORTS_CATEGORY_ID, published_at=NOW)
        session.commit()

    resp = client.get("/search?q=gpt-5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["articles"][0]["id"] == 1


def test_search_empty_query_returns_400(client, fresh_db):
    resp = client.get("/search?q=")
    assert resp.status_code == 400
    assert resp.json()["code"] == "empty_query"


def test_search_no_matches_returns_empty_list(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "OpenAI Releases GPT-5", category_id=TECH_CATEGORY_ID, published_at=NOW)
        session.commit()
    resp = client.get("/search?q=zzz_no_match")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_search_suggest_returns_trie_matches(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "Artificial Intelligence Breakthrough", category_id=TECH_CATEGORY_ID, published_at=NOW)
        session.commit()
    resp = client.get("/search/suggest?prefix=art")
    assert resp.status_code == 200
    assert "artificial" in resp.json()["suggestions"]


def test_trending_counts_topics_within_window(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "A", category_id=TECH_CATEGORY_ID, published_at=NOW)
        seed_article(session, 2, "B", category_id=TECH_CATEGORY_ID, published_at=NOW)
        session.commit()
        from backend.models.models import ArticleTopic, Topic
        session.add(Topic(id=1, name="ai"))
        session.flush()
        session.add(ArticleTopic(article_id=1, topic_id=1))
        session.add(ArticleTopic(article_id=2, topic_id=1))
        session.commit()

    resp = client.get("/trending?limit=5")
    assert resp.status_code == 200
    topics = {t["topic"]: t["score"] for t in resp.json()["topics"]}
    assert "ai" in topics
    assert topics["ai"] > 0


def test_recommendations_returns_related_articles(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "Tech A", category_id=TECH_CATEGORY_ID, published_at=NOW)
        seed_article(session, 2, "Tech B", category_id=TECH_CATEGORY_ID, published_at=NOW)
        seed_article(session, 3, "Sports A", category_id=SPORTS_CATEGORY_ID, published_at=NOW)
        session.commit()

    resp = client.get("/recommendations/1")
    assert resp.status_code == 200
    related_ids = [a["id"] for a in resp.json()["related"]]
    assert 2 in related_ids
    assert 3 not in related_ids


def test_recommendations_unknown_article_returns_404(client, fresh_db):
    resp = client.get("/recommendations/999")
    assert resp.status_code == 404
    assert resp.json()["code"] == "article_not_found"
