"""tests/integration/test_preference_update.py — integration tests for
services.preference_engine against a real (in-memory) database.

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
from backend.services import preference_engine

CATEGORY_ID = 1


@pytest.fixture()
def fresh_db(monkeypatch):
    """Point backend.database.repository at a fresh in-memory SQLite DB."""
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(repository, "SessionLocal", TestSession)
    return TestSession


def test_apply_interaction_creates_row_when_none_exists(fresh_db):
    """A user with no existing preference row must get one created, applying
    the delta on top of the cold-start baseline (0.1).
    """
    with fresh_db() as session:
        session.add(User(id=1, username="tester"))
        session.add(Category(id=CATEGORY_ID, name="Technology", slug="technology"))
        session.commit()

    new_weight = preference_engine.apply_interaction(user_id=1, category_id=CATEGORY_ID, interaction_type="like")
    assert new_weight == pytest.approx(0.20)  # 0.1 baseline + 0.10 like

    with fresh_db() as session:
        row = session.query(UserPreference).filter_by(user_id=1, category_id=CATEGORY_ID).one()
        assert row.weight == pytest.approx(0.20)


def test_apply_interaction_updates_existing_row(fresh_db):
    with fresh_db() as session:
        session.add(User(id=1, username="tester"))
        session.add(Category(id=CATEGORY_ID, name="Technology", slug="technology"))
        session.add(UserPreference(user_id=1, category_id=CATEGORY_ID, topic_id=None, weight=0.5))
        session.commit()

    new_weight = preference_engine.apply_interaction(user_id=1, category_id=CATEGORY_ID, interaction_type="dislike")
    assert new_weight == pytest.approx(0.35)


def test_apply_interaction_for_article_resolves_category(fresh_db):
    with fresh_db() as session:
        session.add(User(id=1, username="tester"))
        session.add(Category(id=CATEGORY_ID, name="Technology", slug="technology"))
        session.add(Article(
            id=1, title="A", content_hash="h1", url="https://example.com/1",
            source_name="Example", category_id=CATEGORY_ID,
            published_at=datetime.datetime.utcnow(),
        ))
        session.commit()

    new_weight = preference_engine.apply_interaction_for_article(user_id=1, article_id=1, interaction_type="save")
    assert new_weight == pytest.approx(0.25)  # 0.1 baseline + 0.15 save


def test_apply_interaction_for_article_with_no_category_returns_none(fresh_db):
    with fresh_db() as session:
        session.add(User(id=1, username="tester"))
        session.add(Article(
            id=1, title="A", content_hash="h1", url="https://example.com/1",
            source_name="Example", category_id=None,
            published_at=datetime.datetime.utcnow(),
        ))
        session.commit()

    assert preference_engine.apply_interaction_for_article(user_id=1, article_id=1, interaction_type="like") is None


def test_apply_interaction_for_nonexistent_article_returns_none(fresh_db):
    with fresh_db() as session:
        session.add(User(id=1, username="tester"))
        session.commit()

    assert preference_engine.apply_interaction_for_article(user_id=1, article_id=999, interaction_type="like") is None
