"""tests/unit/test_hashing.py — unit tests for algorithms.hashing."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.hashing import HashSetIndex, build_index, build_multi_index


def test_build_index_normal_case():
    items = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
    index = build_index(items, key_fn=lambda x: x["id"])
    assert index == {1: items[0], 2: items[1]}


def test_build_index_empty_input():
    assert build_index([], key_fn=lambda x: x) == {}


def test_build_index_single_element():
    items = [{"id": 1}]
    index = build_index(items, key_fn=lambda x: x["id"])
    assert index == {1: items[0]}


def test_build_multi_index_normal_case():
    items = [{"cat": "tech", "id": 1}, {"cat": "tech", "id": 2}, {"cat": "sports", "id": 3}]
    index = build_multi_index(items, key_fn=lambda x: x["cat"])
    assert index["tech"] == [items[0], items[1]]
    assert index["sports"] == [items[2]]


def test_build_multi_index_empty_input():
    assert build_multi_index([], key_fn=lambda x: x) == {}


def test_hashsetindex_normal_case():
    idx = HashSetIndex(["a", "b"])
    assert idx.contains("a") is True
    assert idx.contains("c") is False
    idx.add("c")
    assert idx.contains("c") is True
    assert len(idx) == 3


def test_hashsetindex_empty():
    idx = HashSetIndex()
    assert len(idx) == 0
    assert idx.contains("x") is False
