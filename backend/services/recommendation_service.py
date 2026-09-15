"""backend/services/recommendation_service.py — backs
GET /recommendations/{article_id}.

Primary path: BFS (depth 2) over a graph of recent articles connected by
shared category or >=2 shared topics. Fallback (per the architecture doc):
if the article has no graph edges yet (e.g. it's brand new), rank
same-category recent articles by Jaccard similarity instead.
"""

from backend.algorithms.deduplication import jaccard_similarity, significant_words
from backend.algorithms.graph import bfs
from backend.database import repository
from backend.services.index_manager import build_article_graph

DEFAULT_WINDOW_DAYS = 7
DEFAULT_LIMIT = 5
DEFAULT_MAX_DEPTH = 2


def get_related_articles(
    article_id: int, limit: int = DEFAULT_LIMIT, window_days: int = DEFAULT_WINDOW_DAYS
) -> list[dict]:
    """Return up to `limit` articles related to `article_id`.

    Args:
        article_id: the article being viewed.
        limit: max number of related articles to return.
        window_days: how far back to look for candidate articles.

    Returns:
        Up to `limit` plain article dicts, most related first. Empty list
        if the article doesn't exist in the recent window, or has no
        eligible neighbors/same-category candidates.

    Complexity: O(n^2) to build the bounded recent-window graph (see
    index_manager.build_article_graph), O(V+E) for BFS, O(k log k) to rank
    the k candidates found.
    """
    articles = repository.get_articles_with_topics(days=window_days)
    by_id = {a["id"]: a for a in articles}
    if article_id not in by_id:
        return []

    graph = build_article_graph(articles)
    neighbor_ids = bfs(graph, article_id, max_depth=DEFAULT_MAX_DEPTH)

    if neighbor_ids:
        return _rank_by_shared_topics(by_id[article_id], neighbor_ids, by_id, limit)
    return _jaccard_fallback(by_id[article_id], articles, limit)


def _rank_by_shared_topics(source: dict, neighbor_ids: list, by_id: dict, limit: int) -> list[dict]:
    """Rank BFS neighbors by (shared topic count, recency), per Part 9.

    Complexity: O(k log k) for k neighbors.
    """
    source_topics = set(source["topics"])
    neighbors = [by_id[nid] for nid in neighbor_ids if nid in by_id]
    neighbors.sort(
        key=lambda a: (len(set(a["topics"]) & source_topics), a["published_at"]),
        reverse=True,
    )
    return neighbors[:limit]


def _jaccard_fallback(source: dict, candidates: list[dict], limit: int) -> list[dict]:
    """Rank same-category candidates by Jaccard similarity of significant words.

    Complexity: O(c*w) — c candidates, each an O(w) word-set comparison.
    """
    source_words = significant_words(f"{source['title']} {source['description'] or ''}")
    scored = []
    for candidate in candidates:
        if candidate["id"] == source["id"] or candidate["category"] != source["category"]:
            continue
        candidate_words = significant_words(f"{candidate['title']} {candidate['description'] or ''}")
        similarity = jaccard_similarity(source_words, candidate_words)
        scored.append((similarity, candidate))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [candidate for _, candidate in scored[:limit]]
