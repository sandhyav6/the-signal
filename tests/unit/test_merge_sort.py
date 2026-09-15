"""tests/unit/test_merge_sort.py — unit tests for algorithms.merge_sort."""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.merge_sort import merge_sort


def test_merge_sort_ascending_normal_case():
    items = [{"v": v} for v in [5, 3, 8, 1, 9, 2]]
    result = merge_sort(items, key=lambda x: x["v"])
    assert [x["v"] for x in result] == [1, 2, 3, 5, 8, 9]


def test_merge_sort_descending():
    items = [{"v": v} for v in [5, 3, 8, 1, 9, 2]]
    result = merge_sort(items, key=lambda x: x["v"], reverse=True)
    assert [x["v"] for x in result] == [9, 8, 5, 3, 2, 1]


def test_merge_sort_empty_input():
    assert merge_sort([], key=lambda x: x) == []


def test_merge_sort_single_element():
    items = [{"v": 1}]
    assert merge_sort(items, key=lambda x: x["v"]) == items


def test_merge_sort_does_not_mutate_input():
    items = [{"v": v} for v in [3, 1, 2]]
    original_order = list(items)
    merge_sort(items, key=lambda x: x["v"])
    assert items == original_order


def test_merge_sort_matches_builtin_sorted_on_random_data():
    random.seed(1)
    values = [random.randint(-100, 100) for _ in range(200)]
    items = [{"v": v} for v in values]
    result = merge_sort(items, key=lambda x: x["v"])
    assert [x["v"] for x in result] == sorted(values)


def test_merge_sort_stable_for_equal_keys():
    items = [{"v": 1, "tag": "a"}, {"v": 1, "tag": "b"}, {"v": 0, "tag": "c"}]
    result = merge_sort(items, key=lambda x: x["v"])
    tags_for_v1 = [x["tag"] for x in result if x["v"] == 1]
    assert tags_for_v1 == ["a", "b"]
