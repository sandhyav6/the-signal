"""tests/integration/test_ingestion_pipeline.py — integration tests for the
mock -> normalize -> dedupe -> store ingestion pipeline.

Uses a fresh in-memory SQLite DB per test, patched into
`backend.database.repository` directly (not `backend.database.engine`) —
`repository.py` does `from backend.database.engine import SessionLocal`, a
direct name import, so it binds its own reference at import time; patching
the origin module afterward would not affect it (see tests/unit/
test_phase1_schema.py's seeded_db fixture for the same lesson).
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.database.repository as repository
from backend.models.models import Base
from backend.services import ingestion


@pytest.fixture()
def fresh_db(monkeypatch):
    """Point backend.database.repository at a fresh in-memory SQLite DB."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(repository, "SessionLocal", TestSession)
    return TestSession


def test_ingest_mock_inserts_expected_count_and_skips_known_duplicates(fresh_db):
    """ingest('mock') must skip the 2 known exact-duplicate pairs in the
    mock dataset (Bitcoin price story, India Cricket World Cup story) and
    add every other article.
    """
    raw_articles = ingestion.fetch_mock_articles()
    total_raw = len(raw_articles)

    result = ingestion.ingest("mock")

    assert result["duplicates_skipped"] >= 2
    assert result["added"] == total_raw - result["duplicates_skipped"]

    with fresh_db() as session:
        from backend.models.models import Article
        count = session.query(Article).count()
    assert count == result["added"]


def test_ingest_mock_is_idempotent(fresh_db):
    """Running ingest('mock') a second time must add zero new rows —
    everything is already present by url/content_hash.
    """
    first = ingestion.ingest("mock")
    assert first["added"] > 0

    second = ingestion.ingest("mock")
    assert second["added"] == 0
    assert second["duplicates_skipped"] == first["added"] + first["duplicates_skipped"]


def test_live_fetch_failure_falls_back_to_mock(fresh_db, monkeypatch):
    """A live-fetch failure must be caught (not raised) and fall back to
    mock data, so ingest('live') still returns a valid result.
    """
    import requests

    def _raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("simulated network failure")

    monkeypatch.setattr(ingestion.requests, "get", _raise_connection_error)

    result = ingestion.ingest("live")

    assert isinstance(result, dict)
    assert "added" in result and "duplicates_skipped" in result
    assert result["added"] > 0


@pytest.mark.parametrize(
    "malformed_payload",
    [
        ["not", "a", "dict"],  # a JSON array where an object was expected
        {"status": "error", "message": "rate limited"},  # missing "articles" key
        {"articles": "not-a-list"},  # "articles" present but wrong type
        {"articles": ["a-string-not-an-object"]},  # items aren't article objects
    ],
    ids=["array-not-object", "missing-articles-key", "articles-not-list", "articles-not-objects"],
)
def test_live_fetch_malformed_json_falls_back_to_mock(fresh_db, monkeypatch, malformed_payload):
    """A live response with an unexpected JSON shape must not crash —
    ingest('live') must catch it and fall back to mock data, same as a
    network failure (Part 17 edge case: 'malformed news API JSON').
    """
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return malformed_payload

    monkeypatch.setattr(ingestion.requests, "get", lambda *a, **k: _FakeResponse())

    result = ingestion.ingest("live")

    assert isinstance(result, dict)
    assert "added" in result and "duplicates_skipped" in result
    assert result["added"] > 0  # fell back to the (non-empty) mock dataset
