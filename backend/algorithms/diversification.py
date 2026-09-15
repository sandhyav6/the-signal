"""backend/algorithms/diversification.py — greedy feed diversification.

After heap.top_k ranks candidates by raw score, a single greedy pass caps
how many articles from the same category can appear on one page, so a
user's feed isn't dominated by e.g. all-Technology. Greedy makes one
irrevocable include-or-defer decision per article with no backtracking: not
globally optimal, but O(n) and good enough — the right trade-off here.

Pure function: plain dicts in and out, no ORM/framework objects.
"""

from typing import Callable, TypeVar

T = TypeVar("T")


def greedy_diversify(
    ranked_items: list[T],
    max_per_category: int,
    category_key: Callable[[T], object],
) -> list[T]:
    """Re-order a ranked list so no category exceeds `max_per_category`.

    Args:
        ranked_items: items already sorted by descending score.
        max_per_category: cap on how many items from one category may
            appear before later ones are deferred.
        category_key: function extracting an item's category from it.

    Returns:
        A list of the same items: those kept in rank order first, followed
        by the deferred items (also in their original relative order) —
        deferred items fill later pages rather than being dropped. A cap of
        0 defers every item (nothing is ever under the cap).

    Complexity: O(n) time, O(n) space.
    """
    counts: dict[object, int] = {}
    kept: list[T] = []
    deferred: list[T] = []

    for item in ranked_items:
        category = category_key(item)
        if counts.get(category, 0) < max_per_category:
            kept.append(item)
            counts[category] = counts.get(category, 0) + 1
        else:
            deferred.append(item)

    return kept + deferred
