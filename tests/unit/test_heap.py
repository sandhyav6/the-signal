"""tests/unit/test_heap.py — unit tests for algorithms.heap (MinHeap, top_k)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.heap import MinHeap, top_k


def test_minheap_pop_order_normal_case():
    values = [5, 3, 8, 1, 9, 2]
    heap = MinHeap()
    for value in values:
        heap.push(value, value)
    drained = []
    while len(heap) > 0:
        drained.append(heap.pop()[0])
    assert drained == sorted(values)


def test_minheap_peek_does_not_remove():
    heap = MinHeap()
    heap.push(4, "four")
    heap.push(1, "one")
    assert heap.peek() == (1, "one")
    assert len(heap) == 2


def test_minheap_empty_raises():
    heap = MinHeap()
    try:
        heap.pop()
        assert False, "expected IndexError"
    except IndexError:
        pass


def test_top_k_normal_case():
    items = [{"score": s} for s in [10, 50, 30, 90, 20]]
    result = top_k(items, 3, key=lambda x: x["score"])
    assert [x["score"] for x in result] == [90, 50, 30]


def test_top_k_zero():
    items = [{"score": s} for s in [1, 2, 3]]
    assert top_k(items, 0, key=lambda x: x["score"]) == []


def test_top_k_equals_len_list():
    items = [{"score": s} for s in [3, 1, 2]]
    result = top_k(items, len(items), key=lambda x: x["score"])
    assert [x["score"] for x in result] == [3, 2, 1]


def test_top_k_k_greater_than_len():
    items = [{"score": s} for s in [1, 2]]
    result = top_k(items, 10, key=lambda x: x["score"])
    assert [x["score"] for x in result] == [2, 1]


def test_top_k_empty_input():
    assert top_k([], 5, key=lambda x: x) == []


def test_top_k_single_element():
    items = [{"score": 42}]
    result = top_k(items, 1, key=lambda x: x["score"])
    assert result == items
