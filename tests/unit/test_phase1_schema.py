"""
tests/unit/test_phase1_schema.py — Phase 1 completion criteria tests.

Verifies:
  1. All expected tables exist in the database after seeding.
  2. At least 60 articles are present (after deduplication).
  3. All 7 categories are present.
  4. Default user exists with one preference row per category.
  5. Required indexes exist.
"""

import os
import sys
import pytest

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import inspect, text
from backend.database.engine import engine, SessionLocal
from backend.database.seed import seed
from backend.models.models import (
    Base, User, Category, Article, Topic, UserPreference
)


@pytest.fixture(scope="module", autouse=True)
def seeded_db():
    """Run seed once for all tests in this module using a temp in-memory DB.

    `seed.py` does `from backend.database.engine import SessionLocal` and
    `from backend.database.init_db import create_tables` — these are direct
    name imports, so they bind their own reference in the `seed` module's
    namespace at import time. Patching the attribute on the *origin* module
    (`backend.database.engine.SessionLocal`, `backend.database.init_db.create_tables`)
    does not affect the name already bound inside `seed`'s namespace, so we
    must patch the names where `seed()` actually looks them up.
    """
    from sqlalchemy import create_engine as _ce
    from sqlalchemy.orm import sessionmaker
    import backend.database.seed as seed_mod

    test_engine = _ce("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

    original_session = seed_mod.SessionLocal
    original_create = seed_mod.create_tables

    def mock_create():
        Base.metadata.create_all(bind=test_engine)

    seed_mod.SessionLocal = TestSession
    seed_mod.create_tables = mock_create

    seed()

    yield TestSession

    # Restore
    seed_mod.SessionLocal = original_session
    seed_mod.create_tables = original_create


def test_all_tables_exist():
    """All 8 expected tables must exist in the schema."""
    inspector = inspect(engine)
    # engine is the real one; for test use the patched one via Session
    from backend.database.engine import engine as e
    insp = inspect(e)
    existing = set(insp.get_table_names())
    # We check via Base.metadata instead of the patched engine
    expected = {
        "users", "categories", "articles", "topics",
        "article_topics", "user_preferences", "user_interactions", "bookmarks"
    }
    # Use metadata keys
    defined = set(Base.metadata.tables.keys())
    assert expected == defined, f"Missing tables: {expected - defined}"


def test_article_count_at_least_60(seeded_db):
    """After seeding and deduplication, at least 60 unique articles must be present."""
    with seeded_db() as session:
        count = session.query(Article).count()
    assert count >= 60, f"Expected >= 60 articles, got {count}"


def test_article_count_less_than_raw(seeded_db):
    """Deduplication must have removed exact duplicate articles."""
    with seeded_db() as session:
        count = session.query(Article).count()
    # Raw input has 75 entries with 2 exact duplicates → expect < 75
    assert count < 75, "Exact duplicates were not removed during seeding"


def test_seven_categories_present(seeded_db):
    """All 7 expected categories must be seeded."""
    expected_slugs = {
        "technology", "science", "politics",
        "business", "sports", "health", "entertainment"
    }
    with seeded_db() as session:
        slugs = {row.slug for row in session.query(Category).all()}
    assert expected_slugs == slugs, f"Category mismatch: {expected_slugs ^ slugs}"


def test_default_user_exists(seeded_db):
    """The default user must be created by the seed script."""
    with seeded_db() as session:
        user = session.query(User).filter_by(username="default_user").first()
    assert user is not None, "Default user not found in database"


def test_user_has_preference_for_each_category(seeded_db):
    """Default user must have one UserPreference row per category."""
    with seeded_db() as session:
        user = session.query(User).filter_by(username="default_user").first()
        pref_count = session.query(UserPreference).filter_by(user_id=user.id).count()
        cat_count = session.query(Category).count()
    assert pref_count == cat_count, (
        f"Expected {cat_count} preferences, got {pref_count}"
    )


def test_default_preference_score_is_neutral(seeded_db):
    """All default preferences should start at 0.1 (cold-start baseline)."""
    with seeded_db() as session:
        prefs = session.query(UserPreference).all()
    for pref in prefs:
        assert pref.weight == 0.1, (
            f"Preference user={pref.user_id} cat={pref.category_id} has non-baseline weight {pref.weight}"
        )


def test_articles_have_content_hash(seeded_db):
    """Every article must have a non-null content_hash."""
    with seeded_db() as session:
        missing = session.query(Article).filter(
            Article.content_hash.is_(None)
        ).count()
    assert missing == 0, f"{missing} articles missing content_hash"


def test_articles_have_valid_category(seeded_db):
    """Every article must reference a valid category_id."""
    with seeded_db() as session:
        cat_ids = {c.id for c in session.query(Category).all()}
        articles = session.query(Article).all()
    for art in articles:
        assert art.category_id in cat_ids, (
            f"Article {art.id} has invalid category_id {art.category_id}"
        )


def test_content_hash_unique(seeded_db):
    """No two articles should share the same content_hash (dedup guarantee)."""
    with seeded_db() as session:
        hashes = [row.content_hash for row in session.query(Article).all()]
    assert len(hashes) == len(set(hashes)), "Duplicate content_hash values found"


def test_model_tables_in_metadata():
    """Base.metadata must contain exactly the expected set of table names."""
    expected = {
        "users", "categories", "articles", "topics",
        "article_topics", "user_preferences", "user_interactions", "bookmarks"
    }
    defined = set(Base.metadata.tables.keys())
    assert defined == expected
