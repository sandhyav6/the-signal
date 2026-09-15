"""tests/integration/test_interaction_updates_feed.py — proves the central
dynamic-behavior claim of the whole project: liking an article updates
`user_preferences`, and the *next* feed_service.generate_feed() call
visibly re-ranks as a result. Per the architecture doc, this is "the single
most important integration test in the whole project."

Patches `backend.database.repository.SessionLocal` — see
tests/integration/test_ingestion_pipeline.py for why the origin module
(`backend.database.engine`) is the wrong patch target.
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
from backend.services import feed_service, preference_engine

NOW = datetime.datetime.utcnow()
TECH_CATEGORY_ID = 1
SPORTS_CATEGORY_ID = 2


@pytest.fixture()
def fresh_db(monkeypatch):
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(repository, "SessionLocal", TestSession)
    return TestSession


def test_liking_tech_articles_flips_feed_order_from_sports_to_tech(fresh_db):
    """Sports starts more popular than tech, so it ranks first with equal
    (baseline) preferences. After the user likes tech articles enough times
    to close the popularity gap, the very next generate_feed() call must
    rank tech above sports — proving the preference-update loop actually
    changes what the user sees, not just an internal number.
    """
    with fresh_db() as session:
        session.add(User(id=1, username="tester"))
        session.add(Category(id=TECH_CATEGORY_ID, name="Technology", slug="technology"))
        session.add(Category(id=SPORTS_CATEGORY_ID, name="Sports", slug="sports"))
        session.add(UserPreference(user_id=1, category_id=TECH_CATEGORY_ID, topic_id=None, weight=0.1))
        session.add(UserPreference(user_id=1, category_id=SPORTS_CATEGORY_ID, topic_id=None, weight=0.1))
        session.add(Article(
            id=1, title="Tech Story", content_hash="h1", url="https://example.com/1",
            source_name="Example", category_id=TECH_CATEGORY_ID,
            published_at=NOW, popularity_score=0.3,
        ))
        session.add(Article(
            id=2, title="Sports Story", content_hash="h2", url="https://example.com/2",
            source_name="Example", category_id=SPORTS_CATEGORY_ID,
            published_at=NOW, popularity_score=0.8,
        ))
        session.commit()

    # BEFORE: equal (baseline) preferences, so the popularity gap decides —
    # Sports (more popular) ranks first.
    before = feed_service.generate_feed(user_id=1, k=2, max_per_category=10, now=NOW)
    assert [e["article"]["id"] for e in before] == [2, 1]

    # The user likes the Tech article three times (+0.10 each: 0.1 -> 0.4),
    # which is enough to close the popularity gap (see the module docstring
    # math: 0.35*(40-10) > 0.20*(80-30)).
    for _ in range(3):
        preference_engine.apply_interaction_for_article(user_id=1, article_id=1, interaction_type="like")

    # AFTER: the very next feed call must visibly re-rank — Tech now first.
    after = feed_service.generate_feed(user_id=1, k=2, max_per_category=10, now=NOW)
    assert [e["article"]["id"] for e in after] == [1, 2]

    # And the change is attributable to the interest term specifically.
    tech_entry_after = next(e for e in after if e["article"]["id"] == 1)
    assert tech_entry_after["breakdown"]["interest"]["raw"] == pytest.approx(40.0)
