# Algorithms

Every module in [`backend/algorithms/`](../backend/algorithms/) is pure
Python — plain dicts/lists/sets in and out, no ORM or framework objects —
so each is independently unit-tested (`tests/unit/test_<module>.py`) and
runnable standalone. This is the DAA-report reference for each one:
purpose, pseudocode, complexity, and where it's used in the app.

---

## 1. Hashing (`hashing.py`)

**Purpose:** documents *why* a plain Python `dict` is the right structure
for the app's lookup-heavy operations — Python's `dict` is an open-
addressing hash table, O(1) average insert/lookup/delete.

```
function buildIndex(items, keyFn):
    index = {}
    for item in items:
        index[keyFn(item)] = item
    return index
```

**Complexity:** O(n) to build, O(1) average per lookup afterward.
**Where used:** `content_hash` exact-duplicate lookups (`repository.get_article_by_hash`),
building the Trie/topic-index/graph inputs in `services/index_manager.py`.

---

## 2. String Matching — Rabin-Karp (`string_matching.py`)

**Purpose:** substring search for `GET /search`. Rabin-Karp's rolling
hash lets the search slide across text in O(1) per step instead of O(m).

```
function rabinKarp(text, pattern):
    n, m = len(text), len(pattern)
    patternHash = hash(pattern)
    windowHash = hash(text[0:m])
    matches = []
    for i in 0..n-m:
        if windowHash == patternHash and text[i:i+m] == pattern:
            matches.append(i)
        windowHash = rollHash(windowHash, text[i], text[i+m])  # O(1) update
    return matches
```

**Complexity:** O(n+m) average, O(nm) worst case (hash collisions, resolved
by the verification comparison). A `naive_search` baseline (plain O(nm)
substring scan) lives alongside it for the Phase 9 benchmark comparison.
**Where used:** `GET /search` (`services/search_service.py`).
**Benchmark note:** empirically, `naive_search` was *faster* than
Rabin-Karp in this pure-Python implementation — see `docs/benchmarking.md`
for why (Python-level rolling-hash arithmetic vs. C-level string
comparison).

---

## 3. Trie (`trie.py`)

**Purpose:** autocomplete for the search box (`GET /search/suggest`),
built from article title words and topic names.

```
struct TrieNode: children[char] -> TrieNode, isEndOfWord

function insert(root, word):
    node = root
    for ch in word: node = node.children[ch] or new TrieNode()
    node.isEndOfWord = true

function search(root, prefix):
    node = root
    for ch in prefix: node = node.children[ch]; if null: return []
    return collectAllWords(node, prefix)
```

**Complexity:** O(m) to descend to the prefix node, O(k) to collect k
matches — independent of how many words are stored in total.
**Where used:** `GET /search/suggest`, `services/index_manager.build_trie`.

---

## 4. Heap / Priority Queue (`heap.py`)

**Purpose:** Top-K selection for the main feed and for trending topics.
Hand-written binary min-heap, array-based, ties broken by insertion order
so unorderable payloads (dicts) never need direct comparison.

```
function topK(items, k, key):
    heap = new MinHeap(capacity=k)
    for item in items:
        score = key(item)
        if heap.size < k:
            heap.push(score, item)
        else if score > heap.peek().score:
            heap.pop()
            heap.push(score, item)
    return heap.sortedDescending()
```

**Complexity:** O(n log k) time, O(k) space.
**Where used:** `services/feed_service.generate_feed` (top-20 ranked
feed), `algorithms/trending.compute_trending` (top-N topics).
**Benchmark note:** the heap only pulls ahead of a full sort-then-slice
once n is large enough (~100,000) — at smaller n, Python's C-implemented
`sorted()` wins on raw constant factor. See `docs/benchmarking.md`.

---

## 5. Merge Sort (`merge_sort.py`)

**Purpose:** an explicit, hand-written sort (e.g. "sort saved articles by
date") and the direct benchmark competitor to Python's built-in `sorted()`
(Timsort). Not used on the hot ranking path — `heap.top_k` is used there.

```
function mergeSort(list, key):
    if len(list) <= 1: return list
    mid = len(list) // 2
    left = mergeSort(list[:mid], key)
    right = mergeSort(list[mid:], key)
    return merge(left, right, key)

function merge(left, right, key):
    result = []
    while left and right:
        result.append(left.pop(0) if key(left[0]) >= key(right[0]) else right.pop(0))
    return result + left + right
```

**Complexity:** O(n log n) time, O(n) auxiliary space. Stable (ties keep
their original relative order).
**Where used:** available as a general sort utility; the benchmark suite.

---

## 6. Deduplication (`deduplication.py`)

**Purpose:** two-tier duplicate detection — exact (hash-set membership)
and near-duplicate (Jaccard similarity of significant words).

```
function exactHashCheck(contentHash, existingHashes):
    return contentHash in existingHashes

function jaccard(setA, setB):
    return len(setA ∩ setB) / len(setA ∪ setB)

function isNearDuplicate(setA, setB, threshold=0.7):
    return jaccard(setA, setB) > threshold
```

**Complexity:** O(1) average for the hash check; O(|A|+|B|) for Jaccard.
**Where used:** exact-duplicate checking is currently done inline in
`services/ingestion.py` via `repository.get_article_by_hash` (a
`# TODO Phase 3` marks where it should be swapped for this module's
`exact_hash_check`); near-duplicate detection is validated against the
mock dataset's real near-duplicate pairs in
`tests/integration/test_edge_cases.py` and used by
`services/recommendation_service.py`'s same-category fallback ranking.

---

## 7. Graph + BFS (`graph.py`)

**Purpose:** "Related Articles" — an adjacency-list graph over a bounded
recent window of articles, edges on shared category or ≥2 shared topics.

```
function bfs(graph, start, maxDepth):
    visited = {start}, queue = [(start, 0)], result = []
    while queue:
        node, depth = queue.popleft()
        if depth == maxDepth: continue
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor); result.append(neighbor)
                queue.append((neighbor, depth+1))
    return result
```

**Complexity:** O(V+E) for the BFS traversal; O(n²) to build the graph
itself over n articles (acceptable because the caller bounds n to a small
recent window — see `services/index_manager.build_article_graph`).
**Where used:** `GET /recommendations/{article_id}` and the "Related
articles" panel on every article card
(`services/recommendation_service.py`).

---

## 8. Greedy Diversification (`diversification.py`)

**Purpose:** after Top-K ranks candidates by score, one greedy pass caps
how many articles from one category can appear before deferring the rest.

```
function diversify(rankedArticles, maxPerCategory):
    counts = {}, output = [], deferred = []
    for article in rankedArticles:
        c = article.category
        if counts.get(c, 0) < maxPerCategory:
            output.append(article); counts[c] = counts.get(c,0) + 1
        else:
            deferred.append(article)
    return output + deferred
```

**Complexity:** O(n) time, O(n) space. Not globally optimal — greedy makes
one irrevocable include-or-defer decision per article with no
backtracking, which is the correct trade-off here (optimality isn't worth
the complexity for a feed page).
**Where used:** `services/feed_service.generate_feed`.

---

## 9. Ranking (`ranking.py`)

**Purpose:** the central scoring formula. Returns `(score, breakdown)`
from **one** function so the score and its "why am I seeing this"
explanation can never drift apart.

```
function computeScore(article, userPreferences, now):
    interest    = userPreferences.get(article.category, 0.1) * 100
    recency     = 100 * e^(-λ * ageHours)      # λ = ln(2)/24 (24h half-life)
    popularity  = article.popularity_score * 100
    finalScore  = 0.35*interest + 0.25*recency + 0.20*popularity
                + 0.15*keywordRelevance - 0.05*repetitionPenalty
    return finalScore, breakdown{interest, recency, popularity, ...}
```

**Complexity:** O(1) per article.
**Where used:** `services/feed_service.generate_feed` (every candidate,
before Top-K); `keyword_relevance` and `repetition_penalty` are accepted
as precomputed inputs (0 outside of search/diversification contexts) —
this module never touches search or diversification logic itself.

---

## 10. Trending (`trending.py`)

**Purpose:** "Trending Now" — a HashMap mention-count pass over recent
articles' topics, then Top-K via `heap.top_k`.

```
function computeTrending(articles, windowHours, topN):
    stats = {}   # topic -> [count, totalAgeHours, totalEngagement]
    for article in articles within windowHours:
        for topic in article.topics:
            update stats[topic]
    scored = [(topic, count * recencyFactor(avgAge) * engagementFactor(engagement))
              for topic, (count, ...) in stats.items()]
    return topK(scored, topN, key=score)
```

**Complexity:** O(n) to build the HashMap (n = total topic mentions),
O(n log topN) for the Top-K selection.
**Where used:** `GET /trending` (`services/trending_service.py`), the
"Trending Now" widget on the Home page.
**Design note:** the architecture doc names `recency_factor` and
`engagement_factor` conceptually without fixing exact formulas (unlike
ranking's fully-specified half-life) — this module reuses ranking's
exponential decay for consistency and picks
`engagement_factor = 1 + log(1 + engagement)` so a handful of extra likes
can't let one topic dominate.
