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
from backend.utils.text_cleaning import (
    normalize_title_for_hash,
    strip_html_tags,
    strip_source_suffix,
)

logger = logging.getLogger(__name__)

# NewsAPI replaces articles pulled by their publisher with this placeholder.
_REMOVED_PLACEHOLDER = "[removed]"
UNKNOWN_SOURCE = "Unknown source"


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


def _reject_reason(raw: dict) -> Optional[str]:
    """Return why a raw article can't be stored, or None if it's usable.

    Rejected: no title, NewsAPI's "[Removed]" placeholder, or no url (the
    url is a NOT NULL unique column and the "read at source" link).

    Complexity: O(1).
    """
    raw_title = (raw.get("title") or "").strip()
    if not raw_title:
        return "missing title"
    if raw_title.lower() == _REMOVED_PLACEHOLDER:
        return "removed by publisher"
    if not (raw.get("url") or "").strip():
        return "missing url"
    return None


def normalize(raw: dict) -> Optional[dict]:
    """Normalize a raw article dict into the canonical Article-shaped dict.

    Args:
        raw: raw article dict from any source. Expected keys (all optional
            except title and url): title, description, url, image_url,
            source_name, author, published_at, popularity_score, and the
            optional source hints category_slug and topics.

    Returns:
        A dict with keys: title, description, content_hash, url, image_url,
        source_name, author, category_id, published_at, popularity_score,
        fetched_at, is_duplicate_of, plus category_slug and topics (hints
        the ingestion service resolves and strips before storage).
        Returns None if the article is unusable — see _reject_reason.

    Complexity: O(n) in the combined length of title and description
    (HTML stripping is a single regex pass over each).
    """
    reason = _reject_reason(raw)
    if reason is not None:
        logger.warning("[normalizer.normalize] Rejected article (%s, url=%s)", reason, raw.get("url"))
        return None

    source_name = (raw.get("source_name") or "").strip() or UNKNOWN_SOURCE
    title = strip_source_suffix(strip_html_tags(raw["title"]).strip(), source_name)
    description = strip_html_tags(raw.get("description") or "").strip()

    now = datetime.datetime.utcnow()
    published_at = parse_published_at(raw.get("published_at"), fallback=now)

    return {
        "title": title,
        "description": description,
        "content_hash": _compute_content_hash(title),
        "url": raw["url"].strip(),
        "image_url": raw.get("image_url") or None,
        "source_name": source_name,
        "author": raw.get("author") or None,
        "category_id": None,  # resolved from category_slug by ingestion
        "published_at": published_at,
        "popularity_score": raw.get("popularity_score") or 0,
        "fetched_at": now,
        "is_duplicate_of": None,
        "category_slug": raw.get("category_slug"),
        "topics": [t.lower() for t in raw.get("topics") or [] if isinstance(t, str)],
    }
