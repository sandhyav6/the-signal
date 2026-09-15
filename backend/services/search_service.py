"""backend/services/search_service.py — backs GET /search and
GET /search/suggest. Bridges the pure algorithms/ modules (Rabin-Karp,
Trie) to the database, so route files never call algorithms/ directly.
"""

from backend.algorithms.string_matching import rabin_karp_search
from backend.database import repository
from backend.services.index_manager import build_trie


def search_articles(query: str, page: int = 1, limit: int = 20) -> tuple[list[dict], int]:
    """Find articles whose title or description contains `query`.

    Args:
        query: the search phrase (case-insensitive substring match).
        page: 1-based page number.
        limit: page size.

    Returns:
        (page_of_matching_articles, total_match_count), newest first.

    Complexity: O(a*(n+m)) — a articles, each an O(n+m) Rabin-Karp scan of
    its title+description (n) against the query (m) — plus an O(a log a)
    sort of the matches by recency.
    """
    query_lower = query.lower()
    articles = repository.get_articles_with_topics()

    matches = [
        article
        for article in articles
        if rabin_karp_search(f"{article['title']} {article['description'] or ''}".lower(), query_lower)
    ]
    matches.sort(key=lambda a: a["published_at"], reverse=True)

    total = len(matches)
    start = (page - 1) * limit
    return matches[start:start + limit], total


def suggest(prefix: str, limit: int = 10) -> list[str]:
    """Autocomplete suggestions for a search-box prefix.

    Args:
        prefix: the partial word/phrase typed so far.
        limit: maximum number of suggestions to return.

    Returns:
        Up to `limit` matching words/phrases from article titles and topics.

    Complexity: O(w) to rebuild the Trie (w = total indexed word/phrase
    characters) + O(m+k) to search it (m = len(prefix), k = matches found).
    """
    articles = repository.get_articles_with_topics()
    trie = build_trie(articles)
    return trie.search(prefix, limit=limit)
