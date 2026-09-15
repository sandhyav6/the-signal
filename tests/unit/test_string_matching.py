"""tests/unit/test_string_matching.py — unit tests for algorithms.string_matching."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.string_matching import naive_search, rabin_karp_search


def test_rabin_karp_normal_case_multiple_matches():
    text = "abracadabra"
    assert rabin_karp_search(text, "abra") == [0, 7]


def test_rabin_karp_no_match():
    assert rabin_karp_search("hello world", "xyz") == []


def test_rabin_karp_empty_pattern():
    assert rabin_karp_search("hello", "") == []


def test_rabin_karp_pattern_longer_than_text():
    assert rabin_karp_search("hi", "hello") == []


def test_rabin_karp_single_character_pattern():
    assert rabin_karp_search("aaa", "a") == [0, 1, 2]


def test_rabin_karp_pattern_equals_text():
    assert rabin_karp_search("match", "match") == [0]


def test_rabin_karp_matches_naive_search_agree():
    text = "the quick brown fox jumps over the lazy dog the end"
    for pattern in ["the", "fox", "zzz", "o", ""]:
        assert rabin_karp_search(text, pattern) == naive_search(text, pattern)


def test_naive_search_empty_text():
    assert naive_search("", "a") == []
