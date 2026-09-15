"""backend/algorithms/hashing.py — dict-based hash-index utilities.

Python's `dict` is implemented as an open-addressing hash table: O(1) average
insert/lookup/delete, O(n) worst case under pathological collisions. These
thin wrappers document *why* a plain dict is the right data structure for the
app's lookup-heavy operations (article-by-id, category -> article-id list,
content_hash membership) rather than hiding that fact behind a bigger
abstraction.

Pure functions/classes: plain dicts/lists in and out, no ORM objects.
"""

from typing import Callable, Hashable, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


def build_index(items: list[V], key_fn: Callable[[V], K]) -> dict[K, V]:
    """Build a one-to-one hash index: key -> item.

    Args:
        items: the items to index.
        key_fn: extracts the (unique) key from an item.

    Returns:
        Dict mapping each key to its item. If keys collide, the last item
        with that key wins (matches plain dict-assignment semantics).

    Complexity: O(n) to build, O(1) average per lookup afterward.
    """
    return {key_fn(item): item for item in items}


def build_multi_index(items: list[V], key_fn: Callable[[V], K]) -> dict[K, list[V]]:
    """Build a one-to-many hash index: key -> list of items with that key.

    Used for e.g. category_id -> [article_ids], topic -> [articles].

    Args:
        items: the items to index.
        key_fn: extracts the (non-unique) key from an item.

    Returns:
        Dict mapping each key to the list of items sharing it, in input order.

    Complexity: O(n) to build, O(1) average per key lookup afterward.
    """
    index: dict[K, list[V]] = {}
    for item in items:
        index.setdefault(key_fn(item), []).append(item)
    return index


class HashSetIndex:
    """A thin O(1)-average membership index over hashable keys.

    Used for e.g. the set of content_hash values already seen, so an
    exact-duplicate check never needs a linear scan of all articles.
    """

    def __init__(self, initial: list[K] | None = None) -> None:
        """Args: initial: optional starting keys to seed the set with."""
        self._keys: set[K] = set(initial or [])

    def contains(self, key: K) -> bool:
        """O(1) average membership check."""
        return key in self._keys

    def add(self, key: K) -> None:
        """O(1) average insert."""
        self._keys.add(key)

    def __len__(self) -> int:
        return len(self._keys)
