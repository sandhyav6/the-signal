"""tests/unit/test_trie.py — unit tests for algorithms.trie.Trie."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.trie import Trie


def test_search_normal_case_multiple_matches():
    trie = Trie()
    for word in ["ai", "artificial", "art", "banana"]:
        trie.insert(word)
    results = set(trie.search("ar"))
    assert results == {"artificial", "art"}


def test_search_empty_trie():
    trie = Trie()
    assert trie.search("a") == []


def test_search_empty_prefix():
    trie = Trie()
    trie.insert("hello")
    assert trie.search("") == []


def test_search_prefix_not_found():
    trie = Trie()
    trie.insert("hello")
    assert trie.search("xyz") == []


def test_search_exact_word_is_its_own_prefix():
    trie = Trie()
    trie.insert("cat")
    assert trie.search("cat") == ["cat"]


def test_search_case_insensitive():
    trie = Trie()
    trie.insert("AI")
    assert trie.search("ai") == ["ai"]


def test_search_with_limit():
    trie = Trie()
    for word in ["cat", "car", "cart", "care"]:
        trie.insert(word)
    results = trie.search("ca", limit=2)
    assert len(results) == 2
