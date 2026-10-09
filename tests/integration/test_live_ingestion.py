"""tests/integration/test_live_ingestion.py — the live NewsAPI success path
and its degradation chain (live -> cache -> mock), against a fake NewsAPI.

No real network calls: `news_api_client.requests.get` is replaced by a fake
that answers per requested category, records every call, and can be told to
fail in specific ways.
"""

import datetime

import pytest

from backend.config import settings
from backend.models.models import Article, ArticleTopic
from backend.services import ingestion, news_api_client
from tests.integration.conftest import SPORTS_CATEGORY_ID, TECH_CATEGORY_ID, seed_article, seed_categories, seed_user

NOW = datetime.datetime.utcnow().replace(microsecond=0)


def _item(title, url, source="Wire", description="", minutes_ago=5):
    published = (NOW - datetime.timedelta(minutes=minutes_ago)).isoformat() + "Z"
    return {
        "source": {"id": None, "name": source}, "author": "Staff", "title": title,
        "description": description, "url": url, "urlToImage": None, "publishedAt": published,
    }


FEEDS = {
    "technology": [
        _item("Apple unveils new iPhone with faster chip - The Verge", "https://v.com/1", "The Verge",
              "Apple announced its new iPhone with a faster chip on Tuesday."),
        _item("Apple unveils new iPhone with a faster chip", "https://w.com/1", "Wired",
              "Apple announced its new iPhone with a faster chip on Tuesday."),
        {"title": "[Removed]", "url": "https://removed.com", "source": {"name": "[Removed]"}},
    ],
    "sports": [_item("Lakers beat Celtics in overtime", "https://espn.com/1", "ESPN")],
    "general": [_item("Senate passes election security bill", "https://ap.org/1", "AP")],
}


class _FakeResponse:
    def __init__(self, status, payload):
        self.status_code = status
        self.ok = 200 <= status < 300
        self.reason = "error"
        self._payload = payload

    def json(self):
        return self._payload


class FakeNewsApi:
    """Callable stand-in for requests.get."""

    def __init__(self, feeds=None, failures=None):
        self.feeds = FEEDS if feeds is None else feeds
        self.failures = failures or {}  # category -> (status, payload)
        self.calls = []

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": params, "headers": headers})
        category = params["category"]
        if category in self.failures:
            return _FakeResponse(*self.failures[category])
        return _FakeResponse(200, {"status": "ok", "articles": self.feeds.get(category, [])})


@pytest.fixture()
def live(fresh_db, monkeypatch):
    """Live mode with a fake key, categories + default user seeded, and
    clean refresh/quota state. Returns a function that installs a fake API."""
    monkeypatch.setattr(settings, "news_api_key", "test-key")
    monkeypatch.setattr(settings, "app_env", "live")
    ingestion.reset_state()
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        session.commit()

    def install(fake=None):
        fake = fake or FakeNewsApi()
        monkeypatch.setattr(news_api_client.requests, "get", fake)
        return fake

    yield install
    ingestion.reset_state()


def test_live_ingest_stores_categorized_tagged_articles(live, fresh_db):
    fake = live()
    result = ingestion.ingest("live")

    assert result["source"] == "live"
    assert result["added"] == 4  # 2 iPhone copies + Lakers + Senate; [Removed] rejected
    assert result["near_duplicates"] == 1
    assert result["rejected"] == 1
    assert len(fake.calls) == len(news_api_client.NEWS_API_CATEGORIES) + 1

    with fresh_db() as session:
        verge = session.query(Article).filter_by(url="https://v.com/1").one()
        assert verge.title == "Apple unveils new iPhone with faster chip"  # suffix stripped
        assert verge.category_id == TECH_CATEGORY_ID
        assert session.query(ArticleTopic).filter_by(article_id=verge.id).count() > 0
        lakers = session.query(Article).filter_by(url="https://espn.com/1").one()
        assert lakers.category_id == SPORTS_CATEGORY_ID


def test_api_key_is_sent_as_header_not_query_param(live):
    fake = live()
    ingestion.ingest("live")
    call = fake.calls[0]
    assert call["headers"] == {"X-Api-Key": "test-key"}
    assert "apiKey" not in call["params"]
    assert call["url"].endswith("/top-headlines")


def test_near_duplicate_hidden_from_feed_but_listed_as_coverage(live, client, fresh_db):
    live()
    ingestion.ingest("live")
    with fresh_db() as session:
        original = session.query(Article).filter_by(url="https://v.com/1").one()
        copy = session.query(Article).filter_by(url="https://w.com/1").one()
        assert copy.is_duplicate_of == original.id
        assert original.popularity_score > copy.popularity_score  # coverage boost
        original_id, copy_id = original.id, copy.id

    feed_ids = [e["article"]["id"] for e in client.get("/feed?user_id=1").json()["articles"]]
    assert original_id in feed_ids and copy_id not in feed_ids

    coverage = client.get(f"/articles/{original_id}").json()["coverage"]
    assert [c["source_name"] for c in coverage] == ["Wired"]


def test_refresh_within_cooldown_serves_cache_without_calling_api(live):
    fake = live()
    ingestion.ingest("live")
    calls_after_first = len(fake.calls)

    second = ingestion.ingest("live")

    assert second["source"] == "cache"
    assert second["added"] == 0
    assert len(fake.calls) == calls_after_first


def test_invalid_key_stops_after_first_request_and_uses_cache(live, fresh_db):
    with fresh_db() as session:
        seed_article(session, 1, "Already stored story")
        session.commit()
    fake = live(FakeNewsApi(failures={
        c: (401, {"status": "error", "code": "apiKeyInvalid", "message": "Your API key is invalid."})
        for c in ("technology", "science", "business", "sports", "health", "entertainment", "general")
    }))

    result = ingestion.ingest("live")

    assert len(fake.calls) == 1
    assert news_api_client.requests_used_today() == 1  # unused reservations refunded
    assert result["source"] == "cache"
    assert "invalid" in result["message"].lower()


def test_one_failing_category_keeps_the_rest(live):
    live(FakeNewsApi(failures={"sports": (500, {"status": "error", "code": "unexpectedError"})}))
    result = ingestion.ingest("live")
    assert result["source"] == "live"
    assert result["added"] == 3
    assert "sports" in result["message"]


def test_daily_budget_exhausted_degrades_without_requests(live, monkeypatch):
    monkeypatch.setattr(settings, "news_api_daily_budget", 3)
    fake = live()
    result = ingestion.ingest("live")
    assert fake.calls == []
    assert result["source"] == "mock"  # empty DB -> sample data
    assert "budget" in result["message"]


def test_no_key_with_cached_articles_serves_cache(live, monkeypatch, fresh_db):
    monkeypatch.setattr(settings, "news_api_key", "")
    with fresh_db() as session:
        seed_article(session, 1, "Already stored story")
        session.commit()
    result = ingestion.ingest("live")
    assert result["source"] == "cache"
    assert "NEWS_API_KEY" in result["message"]


def test_status_endpoint_reports_source_and_quota(live, client):
    live()
    client.post("/refresh", json={"mode": "live"})
    status = client.get("/status").json()
    assert status["live_available"] is True
    assert status["default_mode"] == "live"
    assert status["last_source"] == "live"
    assert status["requests_used_today"] == len(news_api_client.NEWS_API_CATEGORIES) + 1
    assert status["article_count"] == 4
    assert status["last_refresh_at"].endswith("Z")


def test_refresh_rejects_unknown_mode(client):
    resp = client.post("/refresh", json={"mode": "rss"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "unknown_mode"


def test_stale_cache_still_renders_feed_latest_and_trending(client, fresh_db):
    """If every stored article is older than the recent windows (a stale
    cache, or the fixed-date sample data), pages widen their window rather
    than going blank."""
    old = NOW - datetime.timedelta(days=30)
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        seed_article(session, 1, "Old tech story", published_at=old)
        seed_article(session, 2, "Older tech story", published_at=old - datetime.timedelta(days=1))
        session.commit()
        from backend.models.models import Topic
        session.add(Topic(id=1, name="chips"))
        session.flush()
        session.add(ArticleTopic(article_id=1, topic_id=1))
        session.commit()

    assert len(client.get("/feed?user_id=1").json()["articles"]) == 2
    assert len(client.get("/feed?user_id=1&type=latest").json()["articles"]) == 2
    assert [t["topic"] for t in client.get("/trending").json()["topics"]] == ["chips"]
    assert [a["id"] for a in client.get("/recommendations/1").json()["related"]] == [2]


def test_maintenance_reprocess_backfills_legacy_rows(client, fresh_db):
    """Rows stored before categorization/topics/near-dup merging existed get
    fixed up by `python -m backend.services.maintenance`, idempotently."""
    from backend.services import maintenance

    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "Lakers beat Celtics in overtime thriller", category_id=SPORTS_CATEGORY_ID)
        seed_article(session, 2, "Lakers beat Celtics in overtime thriller!", category_id=None)
        session.commit()

    first = maintenance.reprocess()
    assert first == {"categorized": 1, "tagged": 2, "linked_duplicates": 1}
    with fresh_db() as session:
        legacy = session.get(Article, 2)
        assert legacy.category_id == SPORTS_CATEGORY_ID
        assert legacy.is_duplicate_of == 1

    assert maintenance.reprocess() == {"categorized": 0, "tagged": 0, "linked_duplicates": 0}
