"""backend/utils/text_cleaning.py — small text-cleaning helpers shared by
ingestion and normalization. Pure string functions, no framework objects.
"""

import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_PUNCT_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")


def strip_html_tags(text: str | None) -> str:
    """Remove HTML tags from text.

    Args:
        text: raw text possibly containing HTML tags, or None.

    Returns:
        Text with tags removed; empty string if input is None/empty.

    Complexity: O(n) in the length of text.
    """
    if not text:
        return ""
    return _HTML_TAG_RE.sub("", text)


def normalize_title_for_hash(title: str) -> str:
    """Lowercase a title and strip punctuation, for dedup hashing.

    Args:
        title: article title.

    Returns:
        Lowercased string with punctuation removed and whitespace collapsed.

    Complexity: O(n) in the length of title.
    """
    lowered = title.strip().lower()
    no_punct = _PUNCT_RE.sub("", lowered)
    return _WHITESPACE_RE.sub(" ", no_punct).strip()
