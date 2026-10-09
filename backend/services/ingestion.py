"""backend/services/ingestion.py — pulls raw articles from mock data or the
live NewsAPI source, and pushes them through the shared pipeline:

    fetch -> normalize -> categorize + tag topics -> exact dedupe
          -> near-duplicate check -> store

Mock and live data go through the exact same path. Live failures degrade
in the order AGENTS.md requires — live -> cached (already-stored articles)
-> mock — and every result says which source was actually used, so the UI
can show a "using sample data" indicator instead of failing.

Runnable standalone:
    python -m backend.services.ingestion --mode live
"""

import argparse
import datetime
import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

from backend.algorithms.classification import classify_category, extract_topics
from backend.algorithms.deduplication import find_near_duplicate
from backend.config import settings
from backend.database import repository
from backend.services import news_api_client
from backend.services.normalizer import normalize

logger = logging.getLogger(__name__)

NEAR_DUPLICATE_WINDOW_HOURS = 48
NEAR_DUPLICATE_THRESHOLD = 0.6
# Popularity boost a story gets each time another outlet's copy of it is
# merged in: wide coverage is the strongest importance signal available.
COVERAGE_POPULARITY_BOOST = 0.05

SOURCE_LIVE, SOURCE_CACHE, SOURCE_MOCK = "live", "cache", "mock"


@dataclass
class IngestionState:
    """What the most recent refresh did — backs GET /status."""
    last_refresh_at: Optional[datetime.datetime] = None
    last_live_fetch_at: Optional[datetime.datetime] = None
    last_source: Optional[str] = None
    last_message: Optional[str] = None
    last_errors: list[str] = field(default_factory=list)


state = IngestionState()
_ingest_lock = threading.Lock()


def reset_state() -> None:
    """Forget refresh history and the API quota (used by tests). O(1)."""
    global state
    state = IngestionState()
    news_api_client.reset_quota()


def fetch_mock_articles() -> list[dict]:
    """Load raw article dicts from data/mock_articles.json.

    Returns:
        List of raw article dicts, exactly as stored in the mock dataset,
        or an empty list if the file is missing or unreadable.

    Complexity: O(n) in file size.
    """
    try:
        with open(settings.mock_data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        logger.error("[ingestion.fetch_mock_articles] Could not load mock data: %s", e)
        return []


def _cooldown_remaining() -> int:
    """Seconds until another live fetch is allowed (0 = allowed now). O(1)."""
    if state.last_live_fetch_at is None:
        return 0
    elapsed = (datetime.datetime.utcnow() - state.last_live_fetch_at).total_seconds()
    return max(0, int(settings.refresh_cooldown_seconds - elapsed))


def _degrade(reason: str) -> tuple[list[dict], str, str]:
    """Live data is unavailable: serve the cache if there is one, else mock.

    Returns:
        (raw_articles_to_ingest, source, user-facing message).

    Complexity: O(1) for the cache case, O(n) to load mock data.
    """
    if repository.count_articles() > 0:
        return [], SOURCE_CACHE, f"{reason} Showing stored articles."
    logger.warning("[ingestion._degrade] %s No cached articles; loading sample data.", reason)
    return fetch_mock_articles(), SOURCE_MOCK, f"{reason} Using sample data."


def _fetch_live() -> tuple[list[dict], str, Optional[str]]:
    """Fetch live articles, degrading to cache/mock when that isn't possible.

    Returns:
        (raw_articles, source, message-or-None).

    Complexity: see news_api_client.fetch_all.
    """
    if not settings.has_news_api_key:
        return _degrade("No NEWS_API_KEY is configured.")
    wait = _cooldown_remaining()
    if wait > 0:
        return [], SOURCE_CACHE, f"Live news was fetched moments ago; next fetch allowed in {wait}s."

    result = news_api_client.fetch_all()
    state.last_errors = result.errors
    if result.fatal_error is None or result.articles:
        state.last_live_fetch_at = datetime.datetime.utcnow()
    if result.articles:
        partial = f"Some sections failed ({', '.join(result.errors)})." if result.errors else None
        return result.articles, SOURCE_LIVE, partial
    reason = result.fatal_error or "no articles returned"
    return _degrade(f"Live news unavailable ({reason}).")


def _resolve_category(normalized: dict, slug_map: dict[str, int]) -> Optional[int]:
    """Map a source category hint to a category id, classifying by keyword
    when the source didn't provide one. O(w) in the article's word count."""
    slug = normalized.get("category_slug")
    if slug is None:
        slug = classify_category(f"{normalized['title']} {normalized['description']}")
    return slug_map.get(slug) if slug else None


def _store_one(normalized: dict, slug_map: dict[str, int]) -> str:
    """Run one normalized article through categorize -> dedupe -> store.

    Returns:
        "added", "duplicate" (exact url/hash match), or "near_duplicate"
        (stored, but linked to an earlier copy of the same story).

    Complexity: O(1) average DB lookups + O(m * w) near-duplicate scan over
    m same-category recent articles.
    """
    category_id = _resolve_category(normalized, slug_map)
    topics = normalized.pop("topics") or extract_topics(normalized["title"], normalized["description"])
    normalized.pop("category_slug", None)
    normalized["category_id"] = category_id

    if repository.get_article_by_hash(normalized["content_hash"]) is not None:
        return "duplicate"
    candidates = repository.get_dedup_candidates(category_id, NEAR_DUPLICATE_WINDOW_HOURS)
    text = f"{normalized['title']} {normalized['description']}"
    original_id = find_near_duplicate(text, candidates, NEAR_DUPLICATE_THRESHOLD)
    normalized["is_duplicate_of"] = original_id

    # insert_article() also de-dupes by url — trust its was_created signal.
    article_id, was_created = repository.insert_article(normalized)
    if not was_created:
        return "duplicate"
    repository.link_article_topics(article_id, topics)
    if original_id is not None:
        repository.adjust_popularity(original_id, COVERAGE_POPULARITY_BOOST)
        return "near_duplicate"
    return "added"


def _store_all(raw_articles: list[dict]) -> dict:
    """Normalize and store a batch. Returns per-outcome counts — "added"
    counts every new row, of which "near_duplicates" were linked to an
    earlier copy of the same story (stored, but hidden from feeds). O(n*m)."""
    counts = {"added": 0, "duplicates_skipped": 0, "near_duplicates": 0, "rejected": 0}
    slug_map = repository.get_category_slug_map()
    for raw in raw_articles:
        normalized = normalize(raw) if isinstance(raw, dict) else None
        if normalized is None:
            counts["rejected"] += 1
            continue
        outcome = _store_one(normalized, slug_map)
        if outcome == "duplicate":
            counts["duplicates_skipped"] += 1
        else:
            counts["added"] += 1
            counts["near_duplicates"] += outcome == "near_duplicate"
    return counts


def ingest(mode: Optional[str] = None) -> dict:
    """Fetch, normalize, deduplicate, and store articles from one source.

    Never raises for source failures: live problems degrade to the cache or
    mock data, and the returned `source`/`message` say what happened.
    Concurrent calls (manual refresh + background refresh) are serialized.

    Args:
        mode: 'mock' or 'live'. Defaults to settings.app_env.

    Returns:
        {"added", "duplicates_skipped", "near_duplicates", "rejected",
         "source": "live"|"cache"|"mock", "message": str|None}

    Complexity: O(n * m) — n fetched articles, each near-duplicate-checked
    against m recent same-category articles (m is small: a 48h window).
    """
    mode = mode or settings.app_env
    with _ingest_lock:
        if mode == SOURCE_LIVE:
            raw_articles, source, message = _fetch_live()
        else:
            raw_articles, source, message = fetch_mock_articles(), SOURCE_MOCK, None
        counts = _store_all(raw_articles)
        state.last_refresh_at = datetime.datetime.utcnow()
        state.last_source, state.last_message = source, message
    return {**counts, "source": source, "message": message}


def _iso(value: Optional[datetime.datetime]) -> Optional[str]:
    """ISO-8601 UTC string (with a trailing Z) or None. O(1)."""
    return value.isoformat() + "Z" if value else None


def get_status() -> dict:
    """Summarize data-source health for GET /status and the UI badge.

    Returns:
        {"default_mode", "live_available", "last_refresh_at", "last_source",
         "last_message", "last_errors", "requests_used_today",
         "daily_request_budget", "cooldown_remaining_seconds",
         "auto_refresh_minutes", "article_count"}

    Complexity: O(1) (one indexed COUNT query).
    """
    return {
        "default_mode": SOURCE_LIVE if settings.is_live_mode else SOURCE_MOCK,
        "live_available": settings.has_news_api_key,
        "last_refresh_at": _iso(state.last_refresh_at),
        "last_source": state.last_source,
        "last_message": state.last_message,
        "last_errors": list(state.last_errors),
        "requests_used_today": news_api_client.requests_used_today(),
        "daily_request_budget": settings.news_api_daily_budget,
        "cooldown_remaining_seconds": _cooldown_remaining(),
        "auto_refresh_minutes": settings.auto_refresh_minutes if settings.is_live_mode else 0,
        "article_count": repository.count_articles(),
    }


def _main() -> None:
    """CLI entry point: `python -m backend.services.ingestion --mode live`."""
    parser = argparse.ArgumentParser(description="Ingest articles into the database.")
    parser.add_argument(
        "--mode", choices=["mock", "live"], default=None,
        help="Ingestion source (default: APP_ENV setting).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = ingest(args.mode)
    print(
        f"Ingestion complete ({result['source']}): added={result['added']} "
        f"near_duplicates={result['near_duplicates']} duplicates_skipped={result['duplicates_skipped']}"
    )
    if result["message"]:
        print(result["message"])


if __name__ == "__main__":
    _main()
