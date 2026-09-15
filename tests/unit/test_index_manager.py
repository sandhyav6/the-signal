"""tests/unit/test_index_manager.py — unit tests for services.index_manager."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.index_manager import (
    build_article_graph,
    build_topic_index,
    build_trie,
)


def test_build_trie_normal_case():
    articles = [
        {"title": "OpenAI Releases GPT-5", "topics": ["artificial intelligence"]},
        {"title": "Apple Unveils M4 Chip", "topics": ["apple"]},
    ]
    trie = build_trie(articles)
    assert "openai" in trie.search("open")
    # topics are inserted as whole phrases (better autocomplete UX than
    # fragmenting a multi-word topic into separate words)
    assert "artificial intelligence" in trie.search("art")


def test_build_trie_empty_input():
    trie = build_trie([])
    assert trie.search("a") == []


def test_build_trie_strips_punctuation():
    trie = build_trie([{"title": "Hello, World!", "topics": []}])
    assert "hello" in trie.search("hel")
    assert "world" in trie.search("wor")


def test_build_topic_index_normal_case():
    articles = [
        {"id": 1, "topics": ["ai", "openai"]},
        {"id": 2, "topics": ["ai"]},
    ]
    index = build_topic_index(articles)
    assert index["ai"] == [1, 2]
    assert index["openai"] == [1]


def test_build_topic_index_empty_input():
    assert build_topic_index([]) == {}


def test_build_article_graph_same_category_edge():
    articles = [
        {"id": 1, "category": "tech", "topics": []},
        {"id": 2, "category": "tech", "topics": []},
        {"id": 3, "category": "sports", "topics": []},
    ]
    graph = build_article_graph(articles)
    assert graph.neighbors(1) == {2}
    assert graph.neighbors(3) == set()


def test_build_article_graph_shared_topics_edge():
    articles = [
        {"id": 1, "category": "tech", "topics": ["ai", "gpt"]},
        {"id": 2, "category": "science", "topics": ["ai", "gpt", "openai"]},
    ]
    graph = build_article_graph(articles, min_shared_topics=2)
    assert graph.neighbors(1) == {2}


def test_build_article_graph_below_threshold_no_edge():
    articles = [
        {"id": 1, "category": "tech", "topics": ["ai"]},
        {"id": 2, "category": "science", "topics": ["gpt"]},
    ]
    graph = build_article_graph(articles, min_shared_topics=2)
    assert graph.neighbors(1) == set()


def test_build_article_graph_empty_input():
    graph = build_article_graph([])
    assert len(graph) == 0


def test_build_article_graph_single_article():
    graph = build_article_graph([{"id": 1, "category": "tech", "topics": []}])
    assert graph.neighbors(1) == set()
