"""backend/algorithms/string_matching.py — Rabin-Karp substring search.

Used by the /search endpoint (Phase 6) to match a query phrase against many
article titles/descriptions. Rabin-Karp's rolling hash lets us slide a
window across `text` in O(1) per step instead of O(m) per step, and the same
rolling-hash idea is reused conceptually for shingling in deduplication.py.

Pure functions: strings in, list of indices out.
"""

_BASE = 256
_MODULUS = 1_000_000_007


def rabin_karp_search(text: str, pattern: str) -> list[int]:
    """Find all starting indices where `pattern` occurs in `text`.

    Args:
        text: the text to search within.
        pattern: the substring to search for.

    Returns:
        List of 0-based starting indices of every occurrence, in order.
        Empty list if pattern is empty, or longer than text, or not found.

    Complexity: O(n+m) average (rolling hash + O(m) verification only on
    hash matches), O(n*m) worst case if many hash collisions occur.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []

    high_order = pow(_BASE, m - 1, _MODULUS)

    pattern_hash = 0
    window_hash = 0
    for i in range(m):
        pattern_hash = (pattern_hash * _BASE + ord(pattern[i])) % _MODULUS
        window_hash = (window_hash * _BASE + ord(text[i])) % _MODULUS

    matches: list[int] = []
    for i in range(n - m + 1):
        if window_hash == pattern_hash and text[i:i + m] == pattern:
            matches.append(i)
        if i < n - m:
            window_hash = (
                (window_hash - ord(text[i]) * high_order) * _BASE + ord(text[i + m])
            ) % _MODULUS

    return matches


def naive_search(text: str, pattern: str) -> list[int]:
    """Brute-force substring search, used as the benchmark baseline.

    Args:
        text: the text to search within.
        pattern: the substring to search for.

    Returns:
        List of 0-based starting indices of every occurrence, in order.

    Complexity: O(n*m) worst case.
    """
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []
    return [i for i in range(n - m + 1) if text[i:i + m] == pattern]
