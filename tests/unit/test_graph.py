"""tests/unit/test_graph.py — unit tests for algorithms.graph (Graph, bfs)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.algorithms.graph import Graph, bfs


def _line_graph():
    """1 - 2 - 3 - 4"""
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 4)
    return g


def test_bfs_normal_case_depth_2():
    g = _line_graph()
    result = bfs(g, 1, max_depth=2)
    assert result == [2, 3]


def test_bfs_depth_1():
    g = _line_graph()
    assert bfs(g, 1, max_depth=1) == [2]


def test_bfs_start_not_in_graph():
    g = _line_graph()
    assert bfs(g, 999, max_depth=2) == []


def test_bfs_isolated_node_has_no_neighbors():
    g = Graph()
    g.add_node("solo")
    assert bfs(g, "solo", max_depth=2) == []


def test_bfs_zero_depth_returns_empty():
    g = _line_graph()
    assert bfs(g, 1, max_depth=0) == []


def test_bfs_single_node_graph():
    g = Graph()
    g.add_node("only")
    assert bfs(g, "only", max_depth=5) == []


def test_graph_add_edge_is_undirected():
    g = Graph()
    g.add_edge("a", "b")
    assert g.neighbors("a") == {"b"}
    assert g.neighbors("b") == {"a"}


def test_graph_no_self_loop():
    g = Graph()
    g.add_edge("a", "a")
    assert g.neighbors("a") == set()
