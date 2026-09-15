"""backend/algorithms/deduplication.py — duplicate-article detection.

Two-tier pipeline: (1) exact duplicates via O(1) hash-set membership on the
normalized-headline hash (already used inline in services/ingestion.py for
Phase 2; this module is the Phase 3 home for that check going forward), and
(2) near-duplicates via Jaccard similarity over each article's significant
words, scoped by the caller to same-category *recent* articles only so the
comparison set stays small.

Pure functions: strings/sets in, bool/float out, no ORM/framework objects.
"""

import re

_WORD_RE = re.compile(r"[a-z0-9]+")

# Common English stopwords that carry no distinguishing signal for
# story-similarity comparison.
_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "with", "as", "by", "from", "its", "it",
    "this", "that", "after", "over", "new", "says",
})


def exact_hash_check(content_hash: str, existing_hashes: set[str]) -> bool:
    """Check whether `content_hash` already exists in `existing_hashes`.

    Args:
        content_hash: the new article's content_hash.
        existing_hashes: the set of hashes already stored.

    Returns:
        True if this is an exact duplicate (hash already seen).

    Complexity: O(1) average (set membership).
    """
    return content_hash in existing_hashes


def significant_words(text: str) -> set[str]:
    """Extract the set of lowercase, stopword-free words from text.

    Used to build the comparison sets for jaccard_similarity.

    Args:
        text: raw text (e.g. an article's title + description).

    Returns:
        Set of significant words.

    Complexity: O(n) in the length of text.
    """
    words = _WORD_RE.findall(text.lower())
    return {w for w in words if w not in _STOPWORDS}


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Compute the Jaccard similarity between two sets: |A∩B| / |A∪B|.

    Args:
        set_a: first set of words.
        set_b: second set of words.

    Returns:
        A float in [0.0, 1.0]. Two empty sets are defined as identical (1.0).

    Complexity: O(|A|+|B|).
    """
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def is_near_duplicate(set_a: set[str], set_b: set[str], threshold: float = 0.7) -> bool:
    """Convenience wrapper: True if jaccard_similarity(set_a, set_b) > threshold.

    Args:
        set_a: first article's significant-word set.
        set_b: second article's significant-word set.
        threshold: similarity threshold above which two articles are
            considered the same story (default 0.7, per the architecture spec).

    Returns:
        True if the two sets are similar enough to be near-duplicates.

    Complexity: O(|A|+|B|).
    """
    return jaccard_similarity(set_a, set_b) > threshold
