"""backend/utils/text_cleaning.py — small text-cleaning helpers shared by
ingestion and normalization. Pure string functions, no framework objects.
"""

import html
import re

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_PUNCT_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")
_TITLE_SUFFIX_RE = re.compile(r"^(?P<body>.+?)\s+[-|–—]\s+(?P<suffix>[^-|–—]{2,60})$")


def strip_html_tags(text: str | None) -> str:
    """Remove HTML tags from text.

    Args:
        text: raw text possibly containing HTML tags, or None.

    Returns:
        Text with tags removed and HTML entities (e.g. "&amp;") decoded;
        empty string if input is None/empty.

    Complexity: O(n) in the length of text.
    """
    if not text:
        return ""
    return html.unescape(_HTML_TAG_RE.sub("", text))


def strip_source_suffix(title: str, source_name: str | None) -> str:
    """Remove a trailing " - Source Name" / " | Source Name" from a headline.

    NewsAPI headlines usually end with the publisher's name ("Fed holds
    rates - Reuters"). Left in, that suffix makes the same story from two
    outlets hash differently and pollutes topic extraction. The suffix is
    only removed when it actually matches the article's source name, so a
    genuine dash inside a headline is left alone.

    Args:
        title: the (HTML-stripped) headline.
        source_name: the article's source name, if known.

    Returns:
        The headline without the matching publisher suffix.

    Complexity: O(n) in the length of title.
    """
    match = _TITLE_SUFFIX_RE.match(title.strip())
    if not match or not source_name:
        return title.strip()
    suffix = match.group("suffix").strip().lower()
    source = source_name.strip().lower()
    if suffix == source or suffix in source or source in suffix:
        return match.group("body").strip()
    return title.strip()


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
