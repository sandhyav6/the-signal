"""backend/services/index_manager.py — builds the in-memory Trie, topic
HashMap, and article-relationship Graph from a set of articles.

Rebuilt fresh from the current candidate window (e.g. the last 7 days) each
time it's needed, rather than updated incrementally per-insert — the window
is kept small enough (per the architecture doc) that a full rebuild stays
cheap without incremental-update bookkeeping.

Orchestration only: bridges plain article dicts into the pure algorithms/
structures (Trie, Graph). No ORM/framework objects handled here.
"""

from backend.algorithms.graph import Graph
from backend.algorithms.trie import Trie

DEFAULT_MIN_SHARED_TOPICS = 2


def build_trie(articles: list[dict]) -> Trie:
    """Build a Trie from every article's title words and topic names.

    Args:
        articles: plain dicts with "title" (str) and optionally "topics"
            (list[str]).

    Returns:
        A Trie ready for prefix search (autocomplete).

    Complexity: O(w) where w = total characters across all inserted words.
    """
    trie = Trie()
    for article in articles:
        for word in article.get("title", "").split():
            cleaned = word.strip(".,!?\"'()")
            if cleaned:
                trie.insert(cleaned)
        for topic in article.get("topics", []):
            trie.insert(topic)
    return trie


def build_topic_index(articles: list[dict]) -> dict[str, list[int]]:
    """Build a topic -> [article_id, ...] HashMap.

    Args:
        articles: plain dicts with "id" and optionally "topics" (list[str]).

    Returns:
        Dict mapping each topic name to the ids of articles mentioning it.

    Complexity: O(n) in total topic mentions.
    """
    index: dict[str, list[int]] = {}
    for article in articles:
        for topic in article.get("topics", []):
            index.setdefault(topic, []).append(article["id"])
    return index


def build_article_graph(
    articles: list[dict], min_shared_topics: int = DEFAULT_MIN_SHARED_TOPICS
) -> Graph:
    """Build a Graph connecting articles that share a category, or share at
    least `min_shared_topics` topics.

    Args:
        articles: plain dicts with "id", "category", and optionally "topics"
            (list[str]).
        min_shared_topics: minimum shared-topic count required to add an
            edge when two articles are in different categories.

    Returns:
        A Graph with one node per article id, edged per the rule above.

    Complexity: O(n^2) over the given article set — acceptable because the
    caller bounds it to a small recent window (e.g. last 7 days), per the
    architecture doc's "keep the subgraph small" guidance.
    """
    graph = Graph()
    for article in articles:
        graph.add_node(article["id"])

    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            a, b = articles[i], articles[j]
            same_category = (
                a.get("category") is not None and a.get("category") == b.get("category")
            )
            shared_topics = len(set(a.get("topics", [])) & set(b.get("topics", [])))
            if same_category or shared_topics >= min_shared_topics:
                graph.add_edge(a["id"], b["id"])

    return graph
