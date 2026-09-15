"""tests/integration/conftest.py — shared fixtures for API integration tests.

Patches `backend.database.repository.SessionLocal` — routes and services
all do `from backend.database import repository` and call `repository.x()`
at request time, so this one patch isolates every DB access made during a
TestClient request. See test_ingestion_pipeline.py for why patching the
origin module (`backend.database.engine`) instead would not work.
"""

import datetime
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.database.repository as repository
from backend.models.models import Article, Base, Category, User, UserPreference
from fastapi.testclient import TestClient

TECH_CATEGORY_ID = 1
SPORTS_CATEGORY_ID = 2


@pytest.fixture()
def fresh_db(monkeypatch):
    """Point backend.database.repository at a fresh in-memory SQLite DB.

    Uses StaticPool (a single connection reused for every checkout) — a
    FastAPI TestClient request runs sync route handlers in a background
    thread, and a plain `sqlite:///:memory:` engine opens a brand-new, empty
    database for each new connection/thread. Without StaticPool, the
    request thread would see a database with no tables at all, even though
    the test's own seeding code (same engine, different connection) just
    populated it.
    """
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(repository, "SessionLocal", TestSession)
    return TestSession


@pytest.fixture()
def client(fresh_db):
    """A FastAPI TestClient backed by the fresh_db fixture."""
    from backend.main import app
    return TestClient(app)


def seed_categories(session):
    session.add(Category(id=TECH_CATEGORY_ID, name="Technology", slug="technology"))
    session.add(Category(id=SPORTS_CATEGORY_ID, name="Sports", slug="sports"))


def seed_user(session, user_id=1, username="tester", with_preferences=True):
    session.add(User(id=user_id, username=username))
    if with_preferences:
        session.add(UserPreference(user_id=user_id, category_id=TECH_CATEGORY_ID, topic_id=None, weight=0.1))
        session.add(UserPreference(user_id=user_id, category_id=SPORTS_CATEGORY_ID, topic_id=None, weight=0.1))


def seed_article(
    session, id_, title, category_id=TECH_CATEGORY_ID, description="", published_at=None,
    popularity=0.5, is_duplicate_of=None, author=None, image_url=None,
):
    session.add(Article(
        id=id_,
        title=title,
        description=description,
        content_hash=f"hash-{id_}",
        url=f"https://example.com/{id_}",
        source_name="Example",
        author=author,
        image_url=image_url,
        category_id=category_id,
        published_at=published_at or datetime.datetime.utcnow(),
        popularity_score=popularity,
        is_duplicate_of=is_duplicate_of,
    ))
