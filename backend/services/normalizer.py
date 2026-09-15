"""backend/services/normalizer.py — normalizes a raw ingested article dict
(from mock JSON, NewsAPI, or RSS) into the canonical dict shape consumed by
`backend.database.repository.insert_article`.

Pure function: plain dicts in, plain dict (or None) out — no ORM/framework
objects, so it is independently testable and reusable across sources.
"""

import datetime
import hashlib
import logging
from typing import Optional

from backend.utils.dates import parse_published_at
from backend.utils.text_cleaning import normalize_title_for_hash, strip_html_tags

logger = logging.getLogger(__name__)


def _compute_content_hash(title: str) -> str:
    """SHA-256 hash of the lowercased, punctuation-stripped title.

    This is the Phase 2 exact-duplicate key. Two articles reporting the same
    story under an (almost) identical headline hash identically.

    Args:
        title: the article's (already HTML-stripped) title.

    Returns:
        Hex-encoded SHA-256 digest.

    Complexity: O(n) in the length of title.
    """
    normalized = normalize_title_for_hash(title)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize(raw: dict) -> Optional[dict]:
    """Normalize a raw article dict into the canonical Article-shaped dict.

    Args:
        raw: raw article dict from any source. Expected keys (all optional
            except title): title, description, url, image_url, source_name,
            author, published_at, popularity_score.

    Returns:
        A dict with keys: title, description, content_hash, url, image_url,
        source_name, author, category_id, published_at, popularity_score,
        fetched_at, is_duplicate_of. Returns None if the article has no
        title — it cannot be shown or meaningfully deduplicated.

    Complexity: O(n) in the combined length of title and description
    (HTML stripping is a single regex pass over each).
    """
    raw_title = raw.get("title")
    if not raw_title or not raw_title.strip():
        logger.warning(
            "[normalizer.normalize] Rejected article with missing title (url=%s)",
            raw.get("url"),
        )
        return None

    title = strip_html_tags(raw_title).strip()
    description = strip_html_tags(raw.get("description") or "")

    now = datetime.datetime.utcnow()
    published_at = parse_published_at(raw.get("published_at"), fallback=now)

    return {
        "title": title,
        "description": description,
        "content_hash": _compute_content_hash(title),
        "url": raw.get("url"),
        "image_url": raw.get("image_url") or None,
        "source_name": raw.get("source_name"),
        "author": raw.get("author") or None,
        "category_id": None,  # categorization happens in Phase 3/4
        "published_at": published_at,
        "popularity_score": raw.get("popularity_score") or 0,
        "fetched_at": now,
        "is_duplicate_of": None,
    }
