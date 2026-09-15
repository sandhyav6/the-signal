"""tests/unit/test_deduplication.py — unit tests for algorithms.deduplication."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.deduplication import (
    exact_hash_check,
    is_near_duplicate,
    jaccard_similarity,
    significant_words,
)


def test_exact_hash_check_normal_case():
    existing = {"hash1", "hash2"}
    assert exact_hash_check("hash1", existing) is True
    assert exact_hash_check("hash3", existing) is False


def test_exact_hash_check_empty_set():
    assert exact_hash_check("hash1", set()) is False


def test_significant_words_strips_stopwords():
    words = significant_words("The Quick Brown Fox and the Lazy Dog")
    assert "the" not in words
    assert "and" not in words
    assert "quick" in words and "brown" in words


def test_jaccard_similarity_normal_case():
    a = {"ai", "openai", "gpt"}
    b = {"ai", "gpt", "model"}
    # intersection={ai,gpt}=2, union={ai,openai,gpt,model}=4
    assert jaccard_similarity(a, b) == 0.5


def test_jaccard_similarity_identical_sets():
    a = {"a", "b"}
    assert jaccard_similarity(a, set(a)) == 1.0


def test_jaccard_similarity_disjoint_sets():
    assert jaccard_similarity({"a"}, {"b"}) == 0.0


def test_jaccard_similarity_both_empty():
    assert jaccard_similarity(set(), set()) == 1.0


def test_jaccard_similarity_one_empty():
    assert jaccard_similarity({"a"}, set()) == 0.0


def test_is_near_duplicate_threshold():
    a = {"a", "b", "c", "d"}
    b = {"a", "b", "c", "e"}  # jaccard = 3/5 = 0.6
    assert is_near_duplicate(a, b, threshold=0.5) is True
    assert is_near_duplicate(a, b, threshold=0.7) is False
