"""backend/algorithms/trie.py — prefix tree for search-box autocomplete.

Built from article title words and a curated topic/keyword list. Lookup time
depends only on prefix length, not on how many words are stored, which is
what makes suggestions feel instant even with a large article corpus.

Pure class: plain strings in and out, no ORM/framework objects.
"""


class _TrieNode:
    """A single node in the trie: a map of next-character -> child node."""

    __slots__ = ("children", "is_end_of_word")

    def __init__(self) -> None:
        self.children: dict[str, "_TrieNode"] = {}
        self.is_end_of_word: bool = False


class Trie:
    """A prefix tree supporting word insertion and prefix-based lookup."""

    def __init__(self) -> None:
        self._root = _TrieNode()

    def insert(self, word: str) -> None:
        """Insert a word into the trie.

        Args:
            word: the word to insert (case-insensitive; stored lowercased).

        Complexity: O(m) where m = len(word).
        """
        word = word.lower().strip()
        if not word:
            return
        node = self._root
        for ch in word:
            node = node.children.setdefault(ch, _TrieNode())
        node.is_end_of_word = True

    def search(self, prefix: str, limit: int | None = None) -> list[str]:
        """Return all inserted words starting with `prefix`.

        Args:
            prefix: the prefix to search for (case-insensitive).
            limit: optional cap on the number of suggestions returned.

        Returns:
            Matching words in the order they're discovered (depth-first);
            empty list if the prefix was never inserted or `prefix` is empty.

        Complexity: O(m) to descend to the prefix node (m = len(prefix)),
        plus O(k) to collect the k matching words below it.
        """
        prefix = prefix.lower().strip()
        if not prefix:
            return []

        node = self._root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]

        results: list[str] = []
        self._collect(node, prefix, results, limit)
        return results

    def _collect(
        self, node: "_TrieNode", prefix: str, results: list[str], limit: int | None
    ) -> None:
        """Depth-first collection of all complete words under `node`."""
        if limit is not None and len(results) >= limit:
            return
        if node.is_end_of_word:
            results.append(prefix)
        for ch, child in node.children.items():
            if limit is not None and len(results) >= limit:
                return
            self._collect(child, prefix + ch, results, limit)
