"""backend/algorithms/merge_sort.py — hand-written merge sort.

Used as an explicit sort utility (e.g. "sort saved articles by date") and as
the direct benchmark competitor to Python's built-in Timsort (`sorted()`)
and to the heap-based Top-K selection in heap.py. Not used on the hot
ranking path in production — heap.top_k is used there since only the top-k
of many candidates is ever needed; using O(n log n) merge sort where
O(n log k) heap selection suffices would be wasted work.

Pure function: plain lists in and out, no ORM/framework objects.
"""

from typing import Callable, TypeVar

T = TypeVar("T")


def merge_sort(items: list[T], key: Callable[[T], float], reverse: bool = False) -> list[T]:
    """Sort `items` by `key` using merge sort.

    Args:
        items: the list to sort (not mutated).
        key: function extracting a comparable value from an item.
        reverse: if True, sort descending; otherwise ascending.

    Returns:
        A new, sorted list.

    Complexity: O(n log n) time, O(n) auxiliary space (out-of-place merge).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key, reverse)
    right = merge_sort(items[mid:], key, reverse)
    return _merge(left, right, key, reverse)


def _merge(left: list[T], right: list[T], key: Callable[[T], float], reverse: bool) -> list[T]:
    """Merge two already-sorted lists into one sorted list. O(len(left)+len(right))."""
    result: list[T] = []
    i = j = 0
    while i < len(left) and j < len(right):
        take_left = key(left[i]) >= key(right[j]) if reverse else key(left[i]) <= key(right[j])
        if take_left:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
