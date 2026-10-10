"""
backend/database/seed.py — Seed the database from mock_articles.json.

Run after init_db.py. Safe to run multiple times (skips existing records).

Usage:
    python -m backend.database.seed
"""

import json
import hashlib
import logging
import datetime
import os
import sys

# Allow running as a script from any directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.exc import SQLAlchemyError

from backend.database.init_db import create_tables
from backend.database.engine import SessionLocal
from backend.models.models import User, Category, Article, Topic, ArticleTopic, UserPreference

logger = logging.getLogger(__name__)

CATEGORIES = [
    {"name": "Technology", "slug": "technology"},
    {"name": "Science", "slug": "science"},
    {"name": "Politics", "slug": "politics"},
    {"name": "Business", "slug": "business"},
    {"name": "Sports", "slug": "sports"},
    {"name": "Health", "slug": "health"},
    {"name": "Entertainment", "slug": "entertainment"},
]

DEFAULT_USER = {"username": "default_user"}


def _compute_hash(title: str, content: str) -> str:
    """SHA-256 hash of normalised title+content for deduplication."""
    raw = (title.strip().lower() + "|" + (content or "").strip().lower())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _seed_categories(session) -> dict[str, int]:
    """Insert categories if missing. Returns {slug: id} mapping."""
    slug_to_id: dict[str, int] = {}
    for cat in CATEGORIES:
        existing = session.query(Category).filter_by(slug=cat["slug"]).first()
        if not existing:
            obj = Category(name=cat["name"], slug=cat["slug"])
            session.add(obj)
            session.flush()
            slug_to_id[cat["slug"]] = obj.id
        else:
            slug_to_id[cat["slug"]] = existing.id
    return slug_to_id


def _seed_default_user(session) -> int:
    """Insert default user if missing. Returns user id."""
    user = session.query(User).filter_by(username=DEFAULT_USER["username"]).first()
    if not user:
        user = User(username=DEFAULT_USER["username"])
        session.add(user)
        session.flush()
    return user.id


def _seed_user_preferences(session, user_id: int, slug_to_id: dict[str, int]) -> None:
    """Create baseline (0.1) preferences for each category (cold-start default)."""
    for slug, cat_id in slug_to_id.items():
        exists = session.query(UserPreference).filter_by(
            user_id=user_id, category_id=cat_id, topic_id=None
        ).first()
        if not exists:
            session.add(UserPreference(user_id=user_id, category_id=cat_id, topic_id=None, weight=0.1))


def _seed_article_topics(session, article: Article, topic_names: list[str]) -> None:
    """Create (or reuse) Topic rows and link them to `article` via ArticleTopic.

    Args:
        session: active SQLAlchemy session.
        article: the already-inserted Article to link topics to.
        topic_names: raw topic name strings from the mock data.

    Complexity: O(t) where t = len(topic_names), each lookup O(1) avg.
    """
    for topic_name in topic_names:
        topic = session.query(Topic).filter_by(name=topic_name.lower()).first()
        if not topic:
            topic = Topic(name=topic_name.lower())
            session.add(topic)
            session.flush()
        exists = session.query(ArticleTopic).filter_by(
            article_id=article.id, topic_id=topic.id
        ).first()
        if not exists:
            session.add(ArticleTopic(article_id=article.id, topic_id=topic.id))


def _seed_articles(session, slug_to_id: dict[str, int], mock_path: str) -> int:
    """Load mock_articles.json and insert new articles. Returns count inserted."""
    with open(mock_path, "r", encoding="utf-8") as f:
        articles_data: list[dict] = json.load(f)

    inserted = 0
    for raw in articles_data:
        content_hash = _compute_hash(raw.get("title", ""), raw.get("content", ""))
        if session.query(Article).filter_by(content_hash=content_hash).first():
            continue  # exact duplicate — skip

        category_slug = raw.get("category_slug", "technology")
        cat_id = slug_to_id.get(category_slug, slug_to_id["technology"])

        published_at = datetime.datetime.fromisoformat(raw["published_at"])

        article = Article(
            title=raw["title"],
            description=raw.get("description"),
            content=raw.get("content"),
            url=raw["url"],
            image_url=raw.get("image_url"),
            source_name=raw["source_name"],
            author=raw.get("author"),
            category_id=cat_id,
            content_hash=content_hash,
            published_at=published_at,
            popularity_score=raw.get("popularity_score", 0.5),
        )
        session.add(article)
        session.flush()

        _seed_article_topics(session, article, raw.get("topics", []))
        inserted += 1
    return inserted


def ensure_base_data() -> None:
    """Create tables, the categories, and the default user + baseline
    preferences if they're missing — everything the app needs to start on
    a brand-new database, without loading the sample articles (ingestion
    fills articles from the live source, or falls back to sample data).

    Called on every app startup, so a fresh deployment needs no manual
    init/seed step. Safe to run repeatedly. Complexity: O(c) for c categories.
    """
    create_tables()
    with SessionLocal() as session:
        try:
            slug_to_id = _seed_categories(session)
            user_id = _seed_default_user(session)
            _seed_user_preferences(session, user_id, slug_to_id)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"[seed.ensure_base_data] Failed: {e}")
            raise


def seed() -> None:
    """Main seed entry point: creates tables then populates all data."""
    create_tables()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mock_path = os.path.join(base_dir, "data", "mock_articles.json")

    if not os.path.exists(mock_path):
        raise FileNotFoundError(f"Mock data not found: {mock_path}")

    with SessionLocal() as session:
        try:
            slug_to_id = _seed_categories(session)
            user_id = _seed_default_user(session)
            _seed_user_preferences(session, user_id, slug_to_id)
            count = _seed_articles(session, slug_to_id, mock_path)
            session.commit()
            logger.info(f"[seed] Inserted {count} articles.")
            print(f"Seeded: {count} new articles inserted.")
        except Exception as e:
            session.rollback()
            logger.error(f"[seed] Failed: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
