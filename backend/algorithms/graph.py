"""backend/algorithms/graph.py — adjacency-list graph + BFS, for "Related
Articles". Nodes are article ids (or topics); edges connect articles that
share enough keywords/category. Built fresh at feed-generation time over a
small, bounded window (e.g. last 7 days) so it stays cheap without special
tricks.

Pure class/function: plain ids in and out, no ORM/framework objects.
"""

from collections import deque


class Graph:
    """An undirected graph stored as an adjacency list (dict of sets)."""

    def __init__(self) -> None:
        self._adjacency: dict[object, set[object]] = {}

    def add_node(self, node: object) -> None:
        """Ensure `node` exists in the graph, with no edges if new. O(1)."""
        self._adjacency.setdefault(node, set())

    def add_edge(self, a: object, b: object) -> None:
        """Add an undirected edge between `a` and `b`. O(1)."""
        self.add_node(a)
        self.add_node(b)
        if a != b:
            self._adjacency[a].add(b)
            self._adjacency[b].add(a)

    def neighbors(self, node: object) -> set[object]:
        """Return the set of nodes directly connected to `node`. O(1)."""
        return set(self._adjacency.get(node, set()))

    def has_node(self, node: object) -> bool:
        """O(1) membership check."""
        return node in self._adjacency

    def __len__(self) -> int:
        return len(self._adjacency)


def bfs(graph: Graph, start: object, max_depth: int = 2) -> list[object]:
    """Breadth-first traversal from `start`, up to `max_depth` hops.

    Args:
        graph: the Graph to traverse.
        start: the starting node.
        max_depth: maximum number of hops from `start` to explore.

    Returns:
        Discovered neighbor nodes (excluding `start` itself), in the order
        they were first reached (closest first). Empty list if `start`
        isn't in the graph or has no reachable neighbors within max_depth.

    Complexity: O(V+E) on the explored subgraph.
    """
    if not graph.has_node(start) or max_depth <= 0:
        return []

    visited = {start}
    queue: deque[tuple[object, int]] = deque([(start, 0)])
    result: list[object] = []

    while queue:
        node, depth = queue.popleft()
        if depth == max_depth:
            continue
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                result.append(neighbor)
                queue.append((neighbor, depth + 1))

    return result
