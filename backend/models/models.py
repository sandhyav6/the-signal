"""
backend/models/models.py — SQLAlchemy ORM models.

Defines all database tables exactly as specified in the architecture document:
  users, categories, articles, topics, article_topics (junction),
  user_preferences, user_interactions, bookmarks.

Key indexes:
  - articles.content_hash       → O(1) exact-duplicate check
  - articles.published_at       → fast recency queries
  - user_interactions(user_id, created_at) → composite index for history
"""

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def _utcnow() -> datetime.datetime:
    """Return timezone-naive UTC datetime (SQLite compatible)."""
    return datetime.datetime.utcnow()


class Base(DeclarativeBase):
    """Base class for all ORM models.

    __allow_unmapped__ permits the plain `field: type = Column(...)` style
    used throughout this file (rather than `Mapped[type]`) under SQLAlchemy
    2.0's Annotated Declarative system.
    """
    __allow_unmapped__ = True


# ─── Users ────────────────────────────────────────────────────────────────────

class User(Base):
    """Represents an application user.

    For this project a single default user (id=1) is used to demonstrate
    personalization without a full auth system.
    """

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    username: str = Column(String(64), nullable=False, unique=True)
    created_at: datetime.datetime = Column(DateTime, default=_utcnow, nullable=False)

    # Relationships
    preferences: list = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    interactions: list = relationship("UserInteraction", back_populates="user", cascade="all, delete-orphan")
    bookmarks: list = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


# ─── Categories ───────────────────────────────────────────────────────────────

class Category(Base):
    """News category (e.g. Technology, Science, Sports).

    A fixed set of categories is seeded on startup.
    """

    __tablename__ = "categories"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(64), nullable=False, unique=True)
    slug: str = Column(String(64), nullable=False, unique=True)  # e.g. "technology"

    # Relationships
    articles: list = relationship("Article", back_populates="category")
    preferences: list = relationship("UserPreference", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"


# ─── Articles ─────────────────────────────────────────────────────────────────

class Article(Base):
    """Represents a single news article.

    content_hash: SHA-256 of normalised title+content — used for O(1) dedup.
    popularity_score: seed value from source (0.0–1.0); updated by interactions.
    """

    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_content_hash", "content_hash"),
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_category_id", "category_id"),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    title: str = Column(String(512), nullable=False)
    description: str = Column(Text, nullable=True)
    content: str = Column(Text, nullable=True)
    url: str = Column(String(1024), nullable=False, unique=True)
    image_url: str = Column(String(1024), nullable=True)
    source_name: str = Column(String(128), nullable=False)
    author: str = Column(String(256), nullable=True)
    # Nullable: categorization happens in Phase 3/4, not at ingestion time (Phase 2).
    category_id: int = Column(Integer, ForeignKey("categories.id"), nullable=True)
    content_hash: str = Column(String(64), nullable=False, unique=True)
    is_duplicate_of: int = Column(Integer, ForeignKey("articles.id"), nullable=True)
    published_at: datetime.datetime = Column(DateTime, nullable=False)
    popularity_score: float = Column(Float, default=0.0, nullable=False)
    like_count: int = Column(Integer, default=0, nullable=False)
    dislike_count: int = Column(Integer, default=0, nullable=False)
    save_count: int = Column(Integer, default=0, nullable=False)
    read_count: int = Column(Integer, default=0, nullable=False)
    fetched_at: datetime.datetime = Column(DateTime, default=_utcnow, nullable=False)

    # Relationships
    category: "Category" = relationship("Category", back_populates="articles")
    topics: list = relationship("ArticleTopic", back_populates="article", cascade="all, delete-orphan")
    interactions: list = relationship("UserInteraction", back_populates="article")
    bookmarks: list = relationship("Bookmark", back_populates="article")

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title[:40]!r}>"


# ─── Topics ───────────────────────────────────────────────────────────────────

class Topic(Base):
    """A keyword/topic extracted from articles (used by Trie and graph).

    Examples: "artificial intelligence", "climate change", "stock market".
    """

    __tablename__ = "topics"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(128), nullable=False, unique=True)

    # Relationships
    articles: list = relationship("ArticleTopic", back_populates="topic")

    def __repr__(self) -> str:
        return f"<Topic id={self.id} name={self.name!r}>"


# ─── Article–Topic junction ───────────────────────────────────────────────────

class ArticleTopic(Base):
    """Many-to-many junction: links articles to their topics."""

    __tablename__ = "article_topics"
    __table_args__ = (
        UniqueConstraint("article_id", "topic_id", name="uq_article_topic"),
        Index("ix_article_topics_topic_id", "topic_id"),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    article_id: int = Column(Integer, ForeignKey("articles.id"), nullable=False)
    topic_id: int = Column(Integer, ForeignKey("topics.id"), nullable=False)

    # Relationships
    article: "Article" = relationship("Article", back_populates="topics")
    topic: "Topic" = relationship("Topic", back_populates="articles")


# ─── User Preferences ─────────────────────────────────────────────────────────

class UserPreference(Base):
    """Per-user interest weight in [0.0, 1.0] for a category OR a topic.

    Exactly one of category_id/topic_id is set per row. Composite primary key
    (user_id, category_id, topic_id) matches the architecture spec; SQLite
    does not enforce NOT NULL on non-INTEGER primary-key columns, so nullable
    category_id/topic_id within the PK is valid here.
    Updated by the preference engine after each user interaction.
    Default weight is 0.1 (cold-start baseline for unselected interests).
    """

    __tablename__ = "user_preferences"

    user_id: int = Column(Integer, ForeignKey("users.id"), primary_key=True)
    category_id: int = Column(Integer, ForeignKey("categories.id"), primary_key=True, nullable=True)
    topic_id: int = Column(Integer, ForeignKey("topics.id"), primary_key=True, nullable=True)
    weight: float = Column(Float, default=0.1, nullable=False)
    updated_at: datetime.datetime = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    # Relationships
    user: "User" = relationship("User", back_populates="preferences")
    category: "Category" = relationship("Category", back_populates="preferences")
    topic: "Topic" = relationship("Topic")

    def __repr__(self) -> str:
        return f"<UserPreference user={self.user_id} cat={self.category_id} topic={self.topic_id} weight={self.weight:.2f}>"


# ─── User Interactions ────────────────────────────────────────────────────────

class UserInteraction(Base):
    """Records every user action (read / like / dislike / save) on an article.

    Composite index on (user_id, created_at) supports efficient history queries.
    """

    __tablename__ = "user_interactions"
    __table_args__ = (
        Index("ix_user_interactions_user_created", "user_id", "created_at"),
    )

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    article_id: int = Column(Integer, ForeignKey("articles.id"), nullable=False)
    interaction_type: str = Column(String(16), nullable=False)  # "read"|"like"|"dislike"|"save"
    created_at: datetime.datetime = Column(DateTime, default=_utcnow, nullable=False)

    # Relationships
    user: "User" = relationship("User", back_populates="interactions")
    article: "Article" = relationship("Article", back_populates="interactions")

    def __repr__(self) -> str:
        return f"<UserInteraction user={self.user_id} article={self.article_id} type={self.interaction_type!r}>"


# ─── Bookmarks ────────────────────────────────────────────────────────────────

class Bookmark(Base):
    """A user's saved article.

    Separate from the save *interaction* so that bookmarks persist even if
    interaction history is pruned.
    """

    __tablename__ = "bookmarks"

    user_id: int = Column(Integer, ForeignKey("users.id"), primary_key=True)
    article_id: int = Column(Integer, ForeignKey("articles.id"), primary_key=True)
    created_at: datetime.datetime = Column(DateTime, default=_utcnow, nullable=False)

    # Relationships
    user: "User" = relationship("User", back_populates="bookmarks")
    article: "Article" = relationship("Article", back_populates="bookmarks")

    def __repr__(self) -> str:
        return f"<Bookmark user={self.user_id} article={self.article_id}>"
