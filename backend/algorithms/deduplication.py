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
from typing import Optional

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


def find_near_duplicate(
    text: str, candidates: list[dict], threshold: float = 0.7
) -> Optional[int]:
    """Find the most similar earlier article that `text` near-duplicates.

    Args:
        text: the new article's title + description.
        candidates: plain dicts with "id", "title" and "description" — the
            caller scopes these to same-category, recent, canonical articles
            so the comparison set stays small.
        threshold: Jaccard similarity above which two articles are treated
            as the same story.

    Returns:
        The id of the best-matching candidate above `threshold`, or None.
        Texts with fewer than 3 significant words are never matched — too
        little signal to call two stories the same.

    Complexity: O(m * w) for m candidates of ~w significant words each.
    """
    words = significant_words(text)
    if len(words) < 3:
        return None
    best_id, best_score = None, threshold
    for candidate in candidates:
        other = significant_words(f"{candidate['title']} {candidate.get('description') or ''}")
        score = jaccard_similarity(words, other)
        if score > best_score:
            best_id, best_score = candidate["id"], score
    return best_id


def link_near_duplicates(
    articles: list[dict], threshold: float = 0.7, window_hours: float = 48.0
) -> dict[int, int]:
    """Batch near-duplicate linking over already-stored articles.

    Sorts by publish time and slides a `window_hours` window over the list,
    comparing each article only against earlier canonical (not-yet-linked)
    articles inside the window — the same story is reported within hours,
    so older articles never need comparing.

    Args:
        articles: dicts with "id", "title", "description" and
            "published_at" (datetime).
        threshold: Jaccard similarity above which two are the same story.
        window_hours: how far back each article looks for an original.

    Returns:
        {duplicate_id: original_id} for every article found to repeat an
        earlier one. The earliest copy of a story is always the original.

    Complexity: O(n log n) sort + O(n * w) comparisons, where w is the
    number of canonical articles inside one window.
    """
    ordered = sorted(articles, key=lambda a: (a["published_at"], a["id"]))
    word_sets = {a["id"]: significant_words(f"{a['title']} {a.get('description') or ''}") for a in ordered}
    links: dict[int, int] = {}
    window: list[dict] = []
    for article in ordered:
        horizon = article["published_at"].timestamp() - window_hours * 3600
        window = [w for w in window if w["published_at"].timestamp() >= horizon]
        words = word_sets[article["id"]]
        best_id, best_score = None, threshold
        for earlier in window:
            score = jaccard_similarity(words, word_sets[earlier["id"]])
            if len(words) >= 3 and score > best_score:
                best_id, best_score = earlier["id"], score
        if best_id is None:
            window.append(article)
        else:
            links[article["id"]] = best_id
    return links
