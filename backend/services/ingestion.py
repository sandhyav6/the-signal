"""backend/services/ingestion.py — pulls raw articles from mock data or a
live NewsAPI source, and pushes them through the shared normalize -> dedupe
-> store pipeline. Mock and live data go through the exact same path.

Runnable standalone (no API route exists yet — that's Phase 6):
    python -m backend.services.ingestion --mode mock
"""

import argparse
import json
import logging

import requests

from backend.config import settings
from backend.database import repository
from backend.services.normalizer import normalize

logger = logging.getLogger(__name__)


def fetch_mock_articles() -> list[dict]:
    """Load raw article dicts from data/mock_articles.json.

    Returns:
        List of raw article dicts, exactly as stored in the mock dataset.

    Complexity: O(n) in file size.
    """
    with open(settings.mock_data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _fallback_to_mock(reason: str, error: Exception) -> list[dict]:
    """Log why the live fetch failed and return the mock dataset instead."""
    logger.error("[ingestion.fetch_live_articles] %s (%s); falling back to mock data", reason, error)
    return fetch_mock_articles()


def _parse_news_api_response(payload: dict) -> list[dict]:
    """Map a NewsAPI-shaped payload's articles into our raw article shape.

    Raises:
        KeyError, TypeError, or AttributeError if `payload` isn't the
        expected {"articles": [{...}, ...]} shape — the caller treats all
        three as "malformed response" and falls back to mock data.
    """
    return [
        {
            "title": a.get("title"),
            "description": a.get("description"),
            "url": a.get("url"),
            "image_url": a.get("urlToImage"),
            "source_name": (a.get("source") or {}).get("name"),
            "author": a.get("author"),
            "published_at": a.get("publishedAt"),
            "popularity_score": 0,
        }
        for a in payload["articles"]
    ]


def fetch_live_articles() -> list[dict]:
    """Fetch raw articles from the configured live NewsAPI endpoint.

    On any request failure (network error, timeout, non-2xx status, or a
    malformed/unexpected-shape JSON response — e.g. missing "articles" key,
    or a JSON array where an object was expected), logs a clear message and
    falls back to mock data instead of raising — ingestion must never crash
    the caller because an external API is unavailable or misbehaving.

    Returns:
        Raw article dicts in the same shape as fetch_mock_articles(), from
        the live API, or from the mock fallback on failure.

    Complexity: O(n) in the number of articles returned by the API.
    """
    try:
        response = requests.get(
            settings.news_api_url,
            params={"apiKey": settings.news_api_key, "language": "en"},
            timeout=10,
        )
        response.raise_for_status()
        return _parse_news_api_response(response.json())
    except requests.RequestException as e:
        return _fallback_to_mock("Live fetch failed", e)
    except (KeyError, TypeError, AttributeError) as e:
        return _fallback_to_mock("Malformed API response", e)


def ingest(mode: str | None = None) -> dict:
    """Fetch, normalize, deduplicate, and store articles from one source.

    Args:
        mode: 'mock' or 'live'. Defaults to settings.app_env.

    Returns:
        {"added": int, "duplicates_skipped": int}

    Complexity: O(n) in the number of fetched articles — each normalize +
    dedup-check + insert is O(1) average via indexed/unique DB lookups.
    """
    mode = mode or settings.app_env
    raw_articles = fetch_live_articles() if mode == "live" else fetch_mock_articles()

    added = 0
    duplicates_skipped = 0
    for raw in raw_articles:
        normalized = normalize(raw)
        if normalized is None:
            continue

        # TODO Phase 3: replace this inline hash check with
        # algorithms/deduplication.py (exact_hash_check + Jaccard near-dup).
        if repository.get_article_by_hash(normalized["content_hash"]) is not None:
            duplicates_skipped += 1
            continue

        # insert_article() also de-dupes by `url` (a broader check than the
        # content_hash pre-check above) — trust its own was_created signal
        # rather than assuming "passed the pre-check" means "was inserted".
        _, was_created = repository.insert_article(normalized)
        if was_created:
            added += 1
        else:
            duplicates_skipped += 1

    return {"added": added, "duplicates_skipped": duplicates_skipped}


def _main() -> None:
    """CLI entry point: `python -m backend.services.ingestion --mode mock`."""
    parser = argparse.ArgumentParser(description="Ingest articles into the database.")
    parser.add_argument(
        "--mode", choices=["mock", "live"], default=None,
        help="Ingestion source (default: APP_ENV setting).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = ingest(args.mode)
    print(f"Ingestion complete: added={result['added']} duplicates_skipped={result['duplicates_skipped']}")


if __name__ == "__main__":
    _main()
