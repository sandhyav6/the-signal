"""backend/algorithms/classification.py — keyword-based category
classification and topic extraction for live articles.

Live NewsAPI articles arrive without our category labels (for its "general"
feed) and without any topic tags at all, but trending, related-articles and
autocomplete all run on topics, and ranking runs on categories. These two
pure functions fill that gap with transparent, explainable heuristics — no
ML model, in keeping with the rest of the ranking engine.

  classify_category: score each category by how many of its keywords appear
      in the text (O(1) hash-set membership per word) and pick the best.
  extract_topics:    rank candidate phrases (capitalized multi-word runs,
      i.e. likely named entities, plus repeated significant words) by a
      simple frequency * length score and keep the top few.

Pure functions: strings in, strings/lists out, no ORM/framework objects.
"""

import re
from typing import Optional

from backend.algorithms.deduplication import _STOPWORDS as _DEDUP_STOPWORDS

# Dedup's stopword list plus the function words / news-speak verbs that are
# common in headlines but never make a meaningful topic on their own.
_STOPWORDS = _DEDUP_STOPWORDS | frozenset({
    "will", "would", "could", "should", "can", "may", "might", "has", "have",
    "had", "been", "being", "be", "not", "no", "about", "into", "than", "then",
    "more", "most", "what", "when", "where", "who", "why", "how", "which",
    "their", "they", "them", "his", "her", "she", "he", "you", "your", "our",
    "we", "us", "all", "any", "some", "out", "up", "down", "off", "just",
    "now", "get", "gets", "got", "said", "say", "report", "reports", "amid",
    "year", "years", "day", "days", "week", "first", "last", "one", "two",
    "here", "there", "these", "those", "also", "still", "back", "make",
    "makes", "time", "news", "latest", "live", "updates", "video", "watch",
})

_WORD_RE = re.compile(r"[a-z0-9]+")
_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-.&]*")

# Keyword sets per category slug. Kept deliberately small and specific —
# a word that plausibly belongs to two categories is left out of both.
CATEGORY_KEYWORDS: dict[str, frozenset[str]] = {
    "technology": frozenset({
        "ai", "software", "app", "apps", "google", "apple", "microsoft", "openai",
        "meta", "chip", "chips", "nvidia", "iphone", "android", "cyber", "hackers",
        "hack", "startup", "robot", "robots", "smartphone", "tech", "algorithm",
        "internet", "data", "cloud", "tesla", "spacex", "gadget", "computing",
    }),
    "science": frozenset({
        "nasa", "scientists", "study", "researchers", "space", "planet", "climate",
        "species", "fossil", "telescope", "physics", "astronomers", "galaxy",
        "asteroid", "moon", "mars", "earthquake", "volcano", "dinosaur", "ocean",
        "experiment", "quantum", "genetic", "evolution",
    }),
    "politics": frozenset({
        "election", "senate", "congress", "president", "governor", "minister",
        "parliament", "democrats", "republicans", "republican", "democrat",
        "trump", "biden", "vote", "voters", "campaign", "lawmakers", "bill",
        "supreme", "court", "white", "policy", "government", "prime",
        "diplomat", "sanctions", "war", "ceasefire", "military", "nato",
    }),
    "business": frozenset({
        "stocks", "stock", "market", "markets", "economy", "inflation", "fed",
        "earnings", "shares", "investors", "revenue", "profit", "bank", "banks",
        "tariffs", "tariff", "trade", "ceo", "company", "merger", "acquisition",
        "dow", "nasdaq", "s&p", "jobs", "unemployment", "oil", "prices",
    }),
    "sports": frozenset({
        "nfl", "nba", "mlb", "nhl", "fifa", "soccer", "football", "basketball",
        "baseball", "tennis", "golf", "olympics", "coach", "quarterback", "season",
        "playoffs", "championship", "league", "match", "tournament", "cricket",
        "game", "score", "team", "athletes", "points", "overtime", "victory",
        "defeat", "striker", "goal", "goals", "innings", "wicket",
    }),
    "health": frozenset({
        "health", "covid", "vaccine", "vaccines", "virus", "disease", "cancer",
        "hospital", "patients", "fda", "cdc", "drug", "drugs", "medical",
        "doctors", "outbreak", "flu", "diabetes", "obesity", "mental", "therapy",
        "treatment", "measles", "infection",
    }),
    "entertainment": frozenset({
        "movie", "film", "films", "box", "netflix", "music", "album", "singer",
        "actor", "actress", "celebrity", "oscars", "grammy", "emmy", "hollywood",
        "tv", "series", "show", "concert", "tour", "disney", "star", "festival",
    }),
}


def classify_category(text: str, keywords: Optional[dict[str, frozenset[str]]] = None) -> Optional[str]:
    """Pick the category slug whose keyword set best matches `text`.

    Args:
        text: free text, typically title + description.
        keywords: {slug: keyword set}; defaults to CATEGORY_KEYWORDS.

    Returns:
        The best-matching slug, or None if no keyword matched at all (the
        caller decides what "unclassified" means). Ties resolve to the
        category listed first in `keywords`, keeping results deterministic.

    Complexity: O(w * c) where w = words in text, c = categories — each
    keyword check is an O(1) average set lookup.
    """
    keywords = keywords or CATEGORY_KEYWORDS
    words = _WORD_RE.findall(text.lower())
    best_slug, best_hits = None, 0
    for slug, vocab in keywords.items():
        hits = sum(1 for w in words if w in vocab)
        if hits > best_hits:
            best_slug, best_hits = slug, hits
    return best_slug


def _is_significant(token: str) -> bool:
    """True if a token is worth keeping as (part of) a topic. O(1)."""
    lowered = token.lower()
    return len(lowered) > 2 and lowered not in _STOPWORDS and not lowered.isdigit()


def _capitalized_phrases(text: str) -> list[str]:
    """Collect runs of 2-3 consecutive capitalized tokens (likely named
    entities such as "Federal Reserve" or "Taylor Swift").

    The first word of a sentence is capitalized for grammatical reasons
    only, so a run is only kept if it has at least two tokens.

    Complexity: O(n) in the number of tokens.
    """
    phrases: list[str] = []
    run: list[str] = []
    for token in _TOKEN_RE.findall(text) + [""]:
        if token[:1].isupper() and _is_significant(token):
            run.append(token.strip(".'"))
            continue
        if 2 <= len(run) <= 3:
            phrases.append(" ".join(run).lower())
        run = []
    return phrases


def _is_title_case(text: str) -> bool:
    """True if most significant words are capitalized ("Fed Holds Rates
    Steady") — in that style capitalization says nothing about named
    entities, so phrase detection is skipped for it. O(n)."""
    tokens = [t for t in _TOKEN_RE.findall(text) if _is_significant(t)]
    if len(tokens) < 3:
        return False
    capitalized = sum(1 for t in tokens if t[:1].isupper())
    return capitalized / len(tokens) > 0.6


def extract_topics(title: str, description: str = "", max_topics: int = 4) -> list[str]:
    """Extract up to `max_topics` lowercase topic strings from an article.

    Candidates are (a) capitalized multi-word phrases and (b) single
    significant words. Each candidate is scored by
    `frequency * (number of words)`, with title mentions counted twice,
    so a named entity in the headline outranks a common word in the body.

    Args:
        title: article headline.
        description: article summary (optional).
        max_topics: maximum number of topics to return.

    Returns:
        Topics sorted by descending score (ties alphabetically), with no
        single word repeated if it already appears inside a chosen phrase.

    Complexity: O(n + u log u) — n tokens to count, u unique candidates
    to sort (u is tiny for a headline + summary).
    """
    counts: dict[str, int] = {}
    for text, weight in ((title, 2), (description or "", 1)):
        phrases = [] if _is_title_case(text) else _capitalized_phrases(text)
        for phrase in phrases:
            counts[phrase] = counts.get(phrase, 0) + weight
        for word in _WORD_RE.findall(text.lower()):
            if _is_significant(word):
                counts[word] = counts.get(word, 0) + weight

    ranked = sorted(counts, key=lambda c: (-counts[c] * len(c.split()), c))
    chosen: list[str] = []
    covered: set[str] = set()
    for candidate in ranked:
        parts = candidate.split()
        if len(parts) == 1 and candidate in covered:
            continue
        chosen.append(candidate)
        covered.update(parts)
        if len(chosen) == max_topics:
            break
    return chosen
