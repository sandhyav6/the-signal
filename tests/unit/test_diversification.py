"""tests/unit/test_diversification.py — unit tests for
algorithms.diversification.greedy_diversify.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.diversification import greedy_diversify


def _article(id_, category):
    return {"id": id_, "category": category}


def test_greedy_diversify_normal_case_caps_per_category():
    ranked = [
        _article(1, "tech"), _article(2, "tech"), _article(3, "tech"),
        _article(4, "tech"), _article(5, "sports"),
    ]
    result = greedy_diversify(ranked, max_per_category=2, category_key=lambda a: a["category"])
    kept_ids = [a["id"] for a in result[:3]]
    assert kept_ids == [1, 2, 5]  # 3rd and 4th tech articles deferred
    assert [a["id"] for a in result[3:]] == [3, 4]


def test_greedy_diversify_empty_input():
    assert greedy_diversify([], max_per_category=3, category_key=lambda a: a) == []


def test_greedy_diversify_cap_zero_defers_everything():
    ranked = [_article(1, "tech"), _article(2, "sports")]
    result = greedy_diversify(ranked, max_per_category=0, category_key=lambda a: a["category"])
    assert [a["id"] for a in result] == [1, 2]  # order preserved, all deferred
    # verify none were "kept" ahead of the cap by re-running with cap=1
    result_cap1 = greedy_diversify(ranked, max_per_category=1, category_key=lambda a: a["category"])
    assert [a["id"] for a in result_cap1] == [1, 2]


def test_greedy_diversify_single_element():
    ranked = [_article(1, "tech")]
    result = greedy_diversify(ranked, max_per_category=1, category_key=lambda a: a["category"])
    assert result == ranked


def test_greedy_diversify_cap_larger_than_list_keeps_all_in_order():
    ranked = [_article(i, "tech") for i in range(3)]
    result = greedy_diversify(ranked, max_per_category=100, category_key=lambda a: a["category"])
    assert result == ranked
