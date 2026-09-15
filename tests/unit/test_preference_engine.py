"""tests/unit/test_preference_engine.py — unit tests for
services.preference_engine.compute_new_weight (pure delta + clamp logic).
"""

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.preference_engine import compute_new_weight


def test_read_increases_weight_by_0_03():
    assert math.isclose(compute_new_weight(0.5, "read"), 0.53)


def test_like_increases_weight_by_0_10():
    assert math.isclose(compute_new_weight(0.5, "like"), 0.60)


def test_save_increases_weight_by_0_15():
    assert math.isclose(compute_new_weight(0.5, "save"), 0.65)


def test_dislike_decreases_weight_by_0_15():
    assert math.isclose(compute_new_weight(0.5, "dislike"), 0.35)


def test_clamped_at_upper_bound_1_0():
    assert compute_new_weight(0.95, "save") == 1.0
    assert compute_new_weight(1.0, "like") == 1.0


def test_clamped_at_lower_bound_0_0():
    assert compute_new_weight(0.05, "dislike") == 0.0
    assert compute_new_weight(0.0, "dislike") == 0.0


def test_unknown_interaction_type_raises():
    with pytest.raises(ValueError):
        compute_new_weight(0.5, "share")


def test_boundary_starting_at_exactly_zero_with_positive_delta():
    assert math.isclose(compute_new_weight(0.0, "read"), 0.03)


def test_boundary_starting_at_exactly_one_with_negative_delta():
    assert math.isclose(compute_new_weight(1.0, "dislike"), 0.85)
