"""tests/integration/test_feed_generation.py — integration tests for
services.feed_service.generate_feed against a fixed DB fixture.

Patches `backend.database.repository.SessionLocal` directly (not
`backend.database.engine`) — repository.py does `from ...engine import
SessionLocal`, a direct name import bound at import time; see
tests/unit/test_phase1_schema.py and tests/integration/
test_ingestion_pipeline.py for the same lesson.
"""

import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.database.repository as repository
from backend.models.models import Article, Base, Category, User, UserPreference
from backend.services import feed_service

NOW = datetime.datetime.utcnow()
TECH_CATEGORY_ID = 1
SPORTS_CATEGORY_ID = 2


@pytest.fixture()
def fresh_db(monkeypatch):
    """Point backend.database.repository at a fresh in-memory SQLite DB."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(repository, "SessionLocal", TestSession)
    return TestSession


def _seed_article(session, id_, category_id, published_at=NOW, popularity=0.5, is_duplicate_of=None):
    session.add(Article(
        id=id_,
        title=f"Article {id_}",
        description="",
        content_hash=f"hash-{id_}",
        url=f"https://example.com/{id_}",
        source_name="Example",
        category_id=category_id,
        published_at=published_at,
        popularity_score=popularity,
        is_duplicate_of=is_duplicate_of,
    ))


def _seed_user_with_preferences(session, tech_weight, sports_weight):
    session.add(Category(id=TECH_CATEGORY_ID, name="Technology", slug="technology"))
    session.add(Category(id=SPORTS_CATEGORY_ID, name="Sports", slug="sports"))
    session.add(User(id=1, username="tester"))
    session.flush()
    session.add(UserPreference(user_id=1, category_id=TECH_CATEGORY_ID, topic_id=None, weight=tech_weight))
    session.add(UserPreference(user_id=1, category_id=SPORTS_CATEGORY_ID, topic_id=None, weight=sports_weight))


def test_generate_feed_ranks_and_diversifies_on_fixed_fixture(fresh_db):
    """A user who strongly prefers Technology over Sports must see all
    Technology articles ranked above all Sports articles, and the
    max_per_category cap must apply within that ranked order.
    """
    with fresh_db() as session:
        _seed_user_with_preferences(session, tech_weight=0.9, sports_weight=0.1)
        for i in range(1, 5):
            _seed_article(session, id_=i, category_id=TECH_CATEGORY_ID)
        for i in range(5, 9):
            _seed_article(session, id_=i, category_id=SPORTS_CATEGORY_ID)
        session.commit()

    result = feed_service.generate_feed(
        user_id=1, k=8, max_per_category=2, recent_days=7, now=NOW
    )

    assert len(result) == 8
    categories = [entry["article"]["category"] for entry in result]
    # First 4 = kept (2 tech + 2 sports, cap=2), last 4 = deferred overflow.
    assert categories[:2] == [TECH_CATEGORY_ID, TECH_CATEGORY_ID]
    assert categories[2:4] == [SPORTS_CATEGORY_ID, SPORTS_CATEGORY_ID]
    assert sorted(categories[4:]) == [TECH_CATEGORY_ID, TECH_CATEGORY_ID, SPORTS_CATEGORY_ID, SPORTS_CATEGORY_ID]

    # Every entry must carry a score and a breakdown consistent with ranking.py.
    for entry in result:
        assert isinstance(entry["score"], float)
        assert "final_score" in entry["breakdown"]


def test_generate_feed_higher_popularity_ranks_higher_within_category(fresh_db):
    """Holding interest/recency equal, higher popularity_score must rank first."""
    with fresh_db() as session:
        _seed_user_with_preferences(session, tech_weight=0.5, sports_weight=0.5)
        _seed_article(session, id_=1, category_id=TECH_CATEGORY_ID, popularity=0.1)
        _seed_article(session, id_=2, category_id=TECH_CATEGORY_ID, popularity=0.9)
        session.commit()

    result = feed_service.generate_feed(user_id=1, k=2, max_per_category=10, now=NOW)
    assert [entry["article"]["id"] for entry in result] == [2, 1]


def test_generate_feed_empty_db_returns_empty_list(fresh_db):
    result = feed_service.generate_feed(user_id=1, now=NOW)
    assert result == []


def test_generate_feed_user_with_no_preferences_uses_baseline(fresh_db):
    """A user with zero UserPreference rows must not crash — ranking.py's
    cold-start baseline (0.1) applies instead.
    """
    with fresh_db() as session:
        session.add(User(id=1, username="new_user"))
        session.add(Category(id=TECH_CATEGORY_ID, name="Technology", slug="technology"))
        _seed_article(session, id_=1, category_id=TECH_CATEGORY_ID)
        session.commit()

    result = feed_service.generate_feed(user_id=1, now=NOW)
    assert len(result) == 1
    assert result[0]["breakdown"]["interest"]["raw"] == 10.0


def test_generate_feed_excludes_marked_duplicates(fresh_db):
    """An article with is_duplicate_of set must never appear in the feed."""
    with fresh_db() as session:
        _seed_user_with_preferences(session, tech_weight=0.5, sports_weight=0.5)
        _seed_article(session, id_=1, category_id=TECH_CATEGORY_ID)
        _seed_article(session, id_=2, category_id=TECH_CATEGORY_ID, is_duplicate_of=1)
        session.commit()

    result = feed_service.generate_feed(user_id=1, now=NOW)
    ids = [entry["article"]["id"] for entry in result]
    assert ids == [1]


def test_generate_feed_single_article(fresh_db):
    with fresh_db() as session:
        _seed_user_with_preferences(session, tech_weight=0.5, sports_weight=0.5)
        _seed_article(session, id_=1, category_id=TECH_CATEGORY_ID)
        session.commit()

    result = feed_service.generate_feed(user_id=1, k=1, now=NOW)
    assert len(result) == 1
    assert result[0]["article"]["id"] == 1


def test_generate_feed_user_with_zero_interests_selected(fresh_db):
    """A user who has preference rows for every category but selected none
    during onboarding (all at the 0.1 cold-start baseline, per Part 7) must
    not crash, and recency/popularity alone decide the order.
    """
    with fresh_db() as session:
        _seed_user_with_preferences(session, tech_weight=0.1, sports_weight=0.1)
        _seed_article(session, id_=1, category_id=TECH_CATEGORY_ID, popularity=0.2)
        _seed_article(session, id_=2, category_id=SPORTS_CATEGORY_ID, popularity=0.9)
        session.commit()

    result = feed_service.generate_feed(user_id=1, k=2, max_per_category=10, now=NOW)
    assert len(result) == 2
    assert [e["breakdown"]["interest"]["raw"] for e in result] == [10.0, 10.0]
    # interest is a tie, so the higher-popularity article ranks first.
    assert result[0]["article"]["id"] == 2


def test_generate_feed_user_with_all_interests_selected(fresh_db):
    """A user who selected every category during onboarding (all at the
    0.7 'selected' weight, per Part 7) must not crash, and diversification
    still applies even though interest doesn't differentiate categories.
    """
    with fresh_db() as session:
        _seed_user_with_preferences(session, tech_weight=0.7, sports_weight=0.7)
        for i in range(1, 4):
            _seed_article(session, id_=i, category_id=TECH_CATEGORY_ID)
        for i in range(4, 7):
            _seed_article(session, id_=i, category_id=SPORTS_CATEGORY_ID)
        session.commit()

    result = feed_service.generate_feed(user_id=1, k=6, max_per_category=1, now=NOW)
    assert len(result) == 6
    kept = result[:2]
    kept_categories = {e["article"]["category"] for e in kept}
    assert kept_categories == {TECH_CATEGORY_ID, SPORTS_CATEGORY_ID}  # cap=1 respected in the kept prefix
