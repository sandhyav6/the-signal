"""backend/database/repository.py — persistence-only CRUD helpers for
articles. No business logic, no algorithm logic — orchestration belongs in
services/, ranking/dedup logic belongs in algorithms/.
"""

import datetime
from typing import Optional

from backend.database.engine import SessionLocal
from backend.models.models import (
    Article,
    ArticleTopic,
    Bookmark,
    Category,
    Topic,
    User,
    UserInteraction,
    UserPreference,
)


def insert_article(article: dict) -> tuple[int, bool]:
    """Insert a new article, or return the id of a pre-existing duplicate.

    An article is considered a duplicate of an existing row if it shares the
    same `url` OR the same `content_hash`. In that case nothing is inserted
    and the existing row's id is returned, so the caller can treat it as a
    duplicate-skip.

    Returns `(id, was_created)` rather than just `id`: a caller-side
    pre-check (e.g. ingestion.ingest()'s `get_article_by_hash` lookup) can
    only see duplicates under its own hash scheme, but this function also
    catches a `url` collision — which happens for real when the same
    mock_articles.json has been loaded through two different hashing paths
    (services.database.seed's title+content hash vs. this ingestion
    pipeline's title-only hash). Without the explicit `was_created` flag,
    a caller that assumes "not pre-flagged as a duplicate" means "newly
    inserted" will over-count `added`.

    Args:
        article: normalized article dict (see services.normalizer.normalize).

    Returns:
        (id, was_created) — was_created is False when an existing row
        (matched by url or content_hash) was returned instead of inserting.

    Complexity: O(1) average (both columns are indexed/unique).
    """
    with SessionLocal() as session:
        existing = (
            session.query(Article)
            .filter(
                (Article.url == article["url"])
                | (Article.content_hash == article["content_hash"])
            )
            .first()
        )
        if existing:
            return existing.id, False

        row = Article(**article)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id, True


def get_article_by_hash(content_hash: str) -> Optional[Article]:
    """Look up an article by its content_hash.

    Args:
        content_hash: the SHA-256 hex digest to search for.

    Returns:
        The matching Article row, or None if no article has this hash.

    Complexity: O(1) average (indexed column).
    """
    with SessionLocal() as session:
        return (
            session.query(Article)
            .filter(Article.content_hash == content_hash)
            .first()
        )


def get_recent_articles(days: int) -> list[Article]:
    """Return all articles published within the last `days` days.

    Args:
        days: how many days back (from now) to include.

    Returns:
        Article rows with published_at >= now - days, newest first.

    Complexity: O(n) where n = number of matching rows (indexed range scan).
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    with SessionLocal() as session:
        return (
            session.query(Article)
            .filter(Article.published_at >= cutoff)
            .order_by(Article.published_at.desc())
            .all()
        )


# When nothing at all was published inside a caller's recent window (a stale
# live cache, or the fixed-date sample dataset), callers widen to this many
# days instead of rendering an empty page.
STALE_FALLBACK_DAYS = 3650


def get_recent_articles_or_stale(days: int) -> list[Article]:
    """get_recent_articles(days), widened to STALE_FALLBACK_DAYS if empty.

    Complexity: O(n) per query; at most two queries.
    """
    return get_recent_articles(days) or get_recent_articles(STALE_FALLBACK_DAYS)


def get_user_category_preferences(user_id: int) -> dict[int, float]:
    """Return a user's per-category interest weights.

    Only rows with category_id set and topic_id NULL are included — topic-
    level preferences are a separate axis not yet consumed by feed_service.

    Args:
        user_id: whose preferences to load.

    Returns:
        {category_id: weight}. Empty dict if the user has no preference rows
        (feed_service/ranking falls back to the cold-start baseline).

    Complexity: O(c) where c = number of categories the user has a row for.
    """
    with SessionLocal() as session:
        rows = (
            session.query(UserPreference)
            .filter(
                UserPreference.user_id == user_id,
                UserPreference.category_id.isnot(None),
                UserPreference.topic_id.is_(None),
            )
            .all()
        )
        return {row.category_id: row.weight for row in rows}


# Cold-start baseline for a category/user pair with no stored preference row
# (matches the default new UserPreference rows are seeded with).
COLD_START_BASELINE_WEIGHT = 0.1


def get_user_category_weight(user_id: int, category_id: int) -> float:
    """Return a user's preference weight for one category.

    Args:
        user_id: the user.
        category_id: the category.

    Returns:
        The stored weight, or COLD_START_BASELINE_WEIGHT if no row exists.

    Complexity: O(1) average (indexed lookup).
    """
    with SessionLocal() as session:
        row = (
            session.query(UserPreference)
            .filter_by(user_id=user_id, category_id=category_id, topic_id=None)
            .first()
        )
        return row.weight if row else COLD_START_BASELINE_WEIGHT


def set_user_category_weight(user_id: int, category_id: int, weight: float) -> None:
    """Create or update (upsert) a user's preference weight for one category.

    Deletes-then-reinserts rather than mutating an existing row in place:
    `user_preferences`'s primary key is (user_id, category_id, topic_id)
    with topic_id NULL for a category-level row, and SQLAlchemy's ORM
    refuses to emit an UPDATE for a row whose primary key includes a NULL
    column (`FlushError: Can't update ... using NULL for primary key
    value`), even though SQLite itself allows it. Delete+insert avoids that
    ORM limitation entirely.

    Args:
        user_id: the user.
        category_id: the category.
        weight: the new weight to store (should already be clamped to [0,1]).

    Complexity: O(1) average (indexed lookup + delete + insert).
    """
    with SessionLocal() as session:
        session.query(UserPreference).filter_by(
            user_id=user_id, category_id=category_id, topic_id=None
        ).delete()
        session.add(
            UserPreference(user_id=user_id, category_id=category_id, topic_id=None, weight=weight)
        )
        session.commit()


def get_article_category(article_id: int) -> Optional[int]:
    """Return an article's category_id.

    Args:
        article_id: the article to look up.

    Returns:
        The article's category_id (may be None if uncategorized), or None
        if no article with this id exists.

    Complexity: O(1) average (primary-key lookup).
    """
    with SessionLocal() as session:
        article = session.get(Article, article_id)
        return article.category_id if article else None


def user_exists(user_id: int) -> bool:
    """Check whether a user with this id exists. O(1) average."""
    with SessionLocal() as session:
        return session.get(User, user_id) is not None


def get_article_by_id(article_id: int) -> Optional[Article]:
    """Look up a single article by primary key. O(1) average."""
    with SessionLocal() as session:
        return session.get(Article, article_id)


def get_categories() -> list[Category]:
    """Return all categories, ordered by name. O(c)."""
    with SessionLocal() as session:
        return session.query(Category).order_by(Category.name).all()


def get_articles_paginated(
    page: int, limit: int, category_id: Optional[int] = None
) -> tuple[list[Article], int]:
    """Return one page of articles (newest first), optionally filtered.

    Args:
        page: 1-based page number.
        limit: page size.
        category_id: if given, only articles in this category.

    Returns:
        (articles_on_this_page, total_matching_count).

    Complexity: O(limit) for the page plus O(1) for the count (indexed).
    """
    with SessionLocal() as session:
        query = session.query(Article)
        if category_id is not None:
            query = query.filter(Article.category_id == category_id)
        total = query.count()
        articles = (
            query.order_by(Article.published_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return articles, total


def add_bookmark(user_id: int, article_id: int) -> bool:
    """Save an article for a user, if not already saved.

    Args:
        user_id: the user.
        article_id: the article to bookmark.

    Returns:
        True if a new bookmark was created, False if it already existed.

    Complexity: O(1) average.
    """
    with SessionLocal() as session:
        exists = (
            session.query(Bookmark).filter_by(user_id=user_id, article_id=article_id).first()
        )
        if exists:
            return False
        session.add(Bookmark(user_id=user_id, article_id=article_id))
        session.commit()
        return True


def get_bookmarked_articles(user_id: int) -> list[Article]:
    """Return a user's saved articles, most recently bookmarked first.

    Complexity: O(b) where b = number of bookmarks for this user.
    """
    with SessionLocal() as session:
        return (
            session.query(Article)
            .join(Bookmark, Bookmark.article_id == Article.id)
            .filter(Bookmark.user_id == user_id)
            .order_by(Bookmark.created_at.desc())
            .all()
        )


def record_interaction(user_id: int, article_id: int, interaction_type: str) -> None:
    """Insert a history row for one user interaction. Pure persistence — no
    validation, no preference/popularity side effects (those are
    services.interaction_service's job).

    Complexity: O(1).
    """
    with SessionLocal() as session:
        session.add(UserInteraction(user_id=user_id, article_id=article_id, interaction_type=interaction_type))
        session.commit()


def get_read_history(user_id: int) -> list[Article]:
    """Return the distinct articles a user has marked 'read', most recent first.

    Complexity: O(h) where h = number of read-interaction rows for this user.
    """
    with SessionLocal() as session:
        rows = (
            session.query(UserInteraction)
            .filter_by(user_id=user_id, interaction_type="read")
            .order_by(UserInteraction.created_at.desc())
            .all()
        )
        seen: set[int] = set()
        articles: list[Article] = []
        for row in rows:
            if row.article_id not in seen:
                seen.add(row.article_id)
                article = session.get(Article, row.article_id)
                if article is not None:
                    articles.append(article)
        return articles


# Fixed popularity_score bump per interaction type — a simple, explainable
# social-proof signal (Part 12: "popularity_score ... derived: likes+saves+reads").
_ENGAGEMENT_POPULARITY_DELTA = {
    "read": 0.01,
    "like": 0.03,
    "save": 0.05,
    "dislike": -0.05,
}
_ENGAGEMENT_COUNT_COLUMN = {
    "read": "read_count",
    "like": "like_count",
    "save": "save_count",
    "dislike": "dislike_count",
}


def bump_article_engagement(article_id: int, interaction_type: str) -> None:
    """Increment an article's engagement counter and nudge its popularity_score.

    Args:
        article_id: the article that was interacted with.
        interaction_type: one of 'read', 'like', 'save', 'dislike'.

    Complexity: O(1). No-op if the article doesn't exist.
    """
    with SessionLocal() as session:
        article = session.get(Article, article_id)
        if article is None:
            return
        count_column = _ENGAGEMENT_COUNT_COLUMN[interaction_type]
        setattr(article, count_column, getattr(article, count_column) + 1)
        delta = _ENGAGEMENT_POPULARITY_DELTA[interaction_type]
        article.popularity_score = max(0.0, min(1.0, article.popularity_score + delta))
        session.commit()


def set_user_preferences_bulk(user_id: int, updates: dict[int, float]) -> dict[int, float]:
    """Directly set (not delta-adjust) a user's weight for each given category.

    Used by PUT /preferences for manual interest editing, as opposed to
    services.preference_engine's interaction-driven deltas.

    Args:
        user_id: the user.
        updates: {category_id: new_weight}. Weights are stored as given —
            callers must validate they're in [0,1] before calling this.

    Returns:
        The user's full updated {category_id: weight} map.

    Complexity: O(u) to apply the updates + O(c) to return the full map.
    """
    for category_id, weight in updates.items():
        set_user_category_weight(user_id, category_id, weight)
    return get_user_category_preferences(user_id)


def _article_with_topics_to_dict(article: Article, topic_names: list[str]) -> dict:
    """Shape one Article row + its topic names into a plain dict.

    Complexity: O(1) (topic_names is already computed by the caller).
    """
    return {
        "id": article.id,
        "title": article.title,
        "description": article.description,
        "category": article.category_id,
        "topics": topic_names,
        "published_at": article.published_at,
        "popularity_score": article.popularity_score,
        "source_name": article.source_name,
        "url": article.url,
        "image_url": article.image_url,
        "like_count": article.like_count,
        "save_count": article.save_count,
        "read_count": article.read_count,
        "is_duplicate_of": article.is_duplicate_of,
    }


def get_articles_with_topics(days: Optional[int] = None) -> list[dict]:
    """Return articles (optionally within the last `days` days) as plain
    dicts, each including its topic names — the shape services.index_manager
    and services.recommendation_service need to build a Trie/Graph.

    Args:
        days: if given, only articles published within this many days.

    Returns:
        Plain dicts with id, title, description, category, topics (list[str]),
        published_at, popularity_score, source_name, url, image_url, the
        engagement counts, and is_duplicate_of (None for canonical stories).

    Complexity: O(n + t) — n articles, t total topic links (one query per
    article's topics; acceptable at this project's data scale).
    """
    with SessionLocal() as session:
        query = session.query(Article)
        if days is not None:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
            query = query.filter(Article.published_at >= cutoff)
        articles = query.all()

        result = []
        for article in articles:
            topic_names = [
                link.topic.name
                for link in session.query(ArticleTopic).filter_by(article_id=article.id).all()
            ]
            result.append(_article_with_topics_to_dict(article, topic_names))
        return result


def get_category_slug_map() -> dict[str, int]:
    """Return {category_slug: category_id} for every category. O(c)."""
    with SessionLocal() as session:
        return {c.slug: c.id for c in session.query(Category).all()}


def count_articles() -> int:
    """Return the total number of stored articles. O(1) (indexed count)."""
    with SessionLocal() as session:
        return session.query(Article).count()


def link_article_topics(article_id: int, topic_names: list[str]) -> None:
    """Create (or reuse) Topic rows and link them to an article.

    Args:
        article_id: the already-inserted article.
        topic_names: lowercase topic strings; duplicates are ignored.

    Complexity: O(t) where t = len(topic_names), each lookup O(1) average
    (topics.name is unique-indexed).
    """
    with SessionLocal() as session:
        for name in dict.fromkeys(topic_names):
            topic = session.query(Topic).filter_by(name=name).first()
            if topic is None:
                topic = Topic(name=name)
                session.add(topic)
                session.flush()
            exists = session.query(ArticleTopic).filter_by(article_id=article_id, topic_id=topic.id).first()
            if exists is None:
                session.add(ArticleTopic(article_id=article_id, topic_id=topic.id))
        session.commit()


def get_dedup_candidates(category_id: Optional[int], hours: int) -> list[dict]:
    """Return recent canonical (non-duplicate) articles in one category, as
    the {id, title, description} dicts the near-duplicate check compares.

    Args:
        category_id: the category to scope to (None = uncategorized).
        hours: how far back (by published_at) to look.

    Complexity: O(m) where m = matching rows (indexed category + date).
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    with SessionLocal() as session:
        query = session.query(Article).filter(
            Article.published_at >= cutoff,
            Article.is_duplicate_of.is_(None),
        )
        if category_id is None:
            query = query.filter(Article.category_id.is_(None))
        else:
            query = query.filter(Article.category_id == category_id)
        return [
            {"id": a.id, "title": a.title, "description": a.description or ""}
            for a in query.all()
        ]


def adjust_popularity(article_id: int, delta: float) -> None:
    """Shift an article's popularity_score by `delta`, clamped to [0, 1].

    Complexity: O(1). No-op if the article doesn't exist.
    """
    with SessionLocal() as session:
        article = session.get(Article, article_id)
        if article is None:
            return
        article.popularity_score = max(0.0, min(1.0, article.popularity_score + delta))
        session.commit()


def get_coverage(article_id: int) -> list[dict]:
    """Return the other outlets' copies of the same story as `article_id`.

    Near-duplicates point at one canonical article via is_duplicate_of, so
    the story's full coverage is the canonical row plus everything linked
    to it — minus the article being viewed.

    Returns:
        [{"id", "source_name", "url"}, ...], oldest first. Empty if the
        article doesn't exist or no other outlet covered the story.

    Complexity: O(d) where d = number of linked copies.
    """
    with SessionLocal() as session:
        article = session.get(Article, article_id)
        if article is None:
            return []
        canonical_id = article.is_duplicate_of or article.id
        rows = (
            session.query(Article)
            .filter((Article.id == canonical_id) | (Article.is_duplicate_of == canonical_id))
            .order_by(Article.published_at)
            .all()
        )
        return [
            {"id": r.id, "source_name": r.source_name, "url": r.url}
            for r in rows if r.id != article_id
        ]


def set_article_category(article_id: int, category_id: Optional[int]) -> None:
    """Set one article's category_id. O(1); no-op if the article is gone."""
    with SessionLocal() as session:
        article = session.get(Article, article_id)
        if article is not None:
            article.category_id = category_id
            session.commit()


def set_duplicate_links(links: dict[int, int]) -> None:
    """Point each duplicate article at its original (is_duplicate_of).

    Args:
        links: {duplicate_id: original_id}.

    Complexity: O(d) primary-key updates in one transaction.
    """
    with SessionLocal() as session:
        for duplicate_id, original_id in links.items():
            article = session.get(Article, duplicate_id)
            if article is not None:
                article.is_duplicate_of = original_id
        session.commit()
