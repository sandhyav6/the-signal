"""backend/algorithms/heap.py — hand-written binary heap, used for Top-K
feed generation and Top-K trending topics.

Why a heap instead of a full sort for Top-K: sorting n candidates to keep
the top k is O(n log n); maintaining a size-k min-heap while scanning is
O(n log k). With n=5000, k=20, that's roughly 60,000 vs 25,000 comparisons —
a real, growing win as n grows. See docs/benchmarking.md for measurements.

Pure class/functions: plain tuples/values in and out, no ORM/framework objects.
"""

from typing import Callable, TypeVar

T = TypeVar("T")


class MinHeap:
    """An array-based binary min-heap over (priority, item) pairs.

    Ties on priority are broken by insertion order (a monotonically
    increasing counter), so items are never compared directly — this lets
    the heap store unorderable payloads (e.g. dicts) safely.
    """

    def __init__(self) -> None:
        self._data: list[tuple[float, int, object]] = []
        self._counter = 0

    def __len__(self) -> int:
        return len(self._data)

    def peek(self) -> tuple[float, object]:
        """Return (priority, item) of the minimum element without removing it.

        Complexity: O(1). Raises IndexError if the heap is empty.
        """
        priority, _, item = self._data[0]
        return priority, item

    def push(self, priority: float, item: object) -> None:
        """Insert (priority, item). Complexity: O(log n)."""
        self._counter += 1
        self._data.append((priority, self._counter, item))
        self._sift_up(len(self._data) - 1)

    def pop(self) -> tuple[float, object]:
        """Remove and return (priority, item) of the minimum element.

        Complexity: O(log n). Raises IndexError if the heap is empty.
        """
        last = self._data.pop()
        if not self._data:
            return last[0], last[2]
        priority, _, item = self._data[0]
        self._data[0] = last
        self._sift_down(0)
        return priority, item

    def _sift_up(self, i: int) -> None:
        while i > 0:
            parent = (i - 1) // 2
            if self._data[i] < self._data[parent]:
                self._data[i], self._data[parent] = self._data[parent], self._data[i]
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        n = len(self._data)
        while True:
            left, right = 2 * i + 1, 2 * i + 2
            smallest = i
            if left < n and self._data[left] < self._data[smallest]:
                smallest = left
            if right < n and self._data[right] < self._data[smallest]:
                smallest = right
            if smallest == i:
                break
            self._data[i], self._data[smallest] = self._data[smallest], self._data[i]
            i = smallest


def top_k(items: list[T], k: int, key: Callable[[T], float]) -> list[T]:
    """Select the top-k items by `key`, descending, using a size-k min-heap.

    Args:
        items: candidate items.
        k: how many top items to return. k<=0 returns [].
        key: function extracting a numeric score from an item.

    Returns:
        The k items with the highest key(item), sorted descending. If
        len(items) <= k, returns all items sorted descending.

    Complexity: O(n log k) time, O(k) space — see module docstring.
    """
    if k <= 0 or not items:
        return []

    heap = MinHeap()
    for item in items:
        score = key(item)
        if len(heap) < k:
            heap.push(score, item)
        elif score > heap.peek()[0]:
            heap.pop()
            heap.push(score, item)

    result = [heap.pop() for _ in range(len(heap))]
    result.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in result]
