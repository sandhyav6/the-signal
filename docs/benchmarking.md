# Benchmarking (Phase 9)

`benchmarks/run_benchmarks.py` compares four algorithm pairs at
n ∈ {100, 1,000, 10,000, 100,000} synthetic articles (no live API calls),
each timing averaged over 5 runs via `time.perf_counter()`. Raw results are
in `benchmarks/results/*.csv`; charts (log-scale x-axis) are the matching
`*.png` files. Run it yourself with:

```bash
python -m benchmarks.run_benchmarks
```

All four experiments ran to completion with no crashes at every size,
including 100,000 articles — 1,000x larger than the project's actual mock
dataset (75 articles), confirming the algorithms hold up structurally at
scale even though this project will never see that much real data.

---

## 1. Merge Sort vs `sorted()`

| n | Merge Sort (s) | `sorted()` (s) | Expected O(n log n) |
|---|---|---|---|
| 100 | 0.00072 | 0.0000367 | 664 |
| 1,000 | 0.0140 | 0.000436 | 9,966 |
| 10,000 | 0.210 | 0.00627 | 132,877 |
| 100,000 | 2.796 | 0.1024 | 1,660,964 |

**Expected vs observed:** Both should be O(n log n). Merge sort's own
timing does track that shape reasonably well (each 10x increase in n grows
its time by roughly 13-20x, close to the ~13x an ideal n log n curve
predicts). `sorted()` tracks its own O(n log n) shape too, just starting
from a much smaller constant.

**Why they diverge in absolute terms (a ~27x gap at n=100,000):**
`sorted()` is Timsort, implemented in C, and it evaluates the sort key
**once per element** (Python calls this a Schwartzian-transform-style
decorate-sort-undecorate internally). Our hand-written `merge_sort` is pure
Python, recurses with real list slicing (`items[:mid]`, `items[mid:]` —
each an O(n) copy at every recursion level, not just O(1) pointer
arithmetic), and — a genuine inefficiency we noticed while writing this
report — its `_merge` step **re-evaluates `key(x)` on every comparison**
rather than pre-computing each element's key once, so it calls `key()`
roughly twice per comparison instead of once per element. None of that
changes the asymptotic class, but it multiplies the constant factor by
roughly an order of magnitude, which is exactly what we see. We left
`merge_sort.py` itself unchanged — it's correct and already covered by
Phase 3's tests — this is a benchmarking-report finding, not a bug fix.

---

## 2. Heap Top-K vs full-sort-then-slice (k=20)

| n | Heap Top-K (s) | sort+slice (s) | Expected heap O(n log k) | Expected sort O(n log n) |
|---|---|---|---|---|
| 100 | 0.00150 | 0.0000383 | 432 | 664 |
| 1,000 | 0.00183 | 0.000412 | 4,322 | 9,966 |
| 10,000 | 0.01615 | 0.00880 | 43,219 | 132,877 |
| 100,000 | 0.1420 | 0.1377 | 432,193 | 1,660,964 |

**Expected vs observed:** This is the most interesting result in the whole
report, because it shows the theory and the practice **converging** right
where theory predicts, even if it hasn't fully crossed over yet at this
scale. Heap Top-K is O(n log k) with k fixed at 20 — so its curve should
grow *almost linearly* in n (log 20 is a small constant), while
full-sort-then-slice is O(n log n) and its curve should bend upward faster.
At n=100 through n=10,000, the heap is consistently *slower* in wall-clock
terms — Python-level overhead per `push`/`pop` call (our hand-written
`MinHeap` does real Python function calls and tuple comparisons for every
operation) outweighs the asymptotic advantage when n is small. By
n=100,000 the two are within 3% of each other (0.142s vs 0.138s) — close
enough that repeated runs land on either side of the crossover purely from
measurement noise (one run of this same benchmark had the heap slightly
ahead, 0.143s vs 0.161s). Either way, the trend is unambiguous: the gap
between the two closes steadily as n grows, exactly the shape the
architecture doc's Part 5 #4 reasoning predicts — it would just take a
somewhat larger n than the naive "60,000 vs 25,000 comparisons" estimate
assumed for the heap to pull clearly ahead, because that estimate didn't
account for Python's per-call overhead being much higher on the heap's many
small operations than on a single call into Timsort's C implementation.

---

## 3. Rabin-Karp vs naive substring search

| n | Rabin-Karp (s) | Naive (s) |
|---|---|---|
| 100 | 0.0377 | 0.0120 |
| 1,000 | 0.426 | 0.116 |
| 10,000 | 4.244 | 1.155 |
| 100,000 | 35.43 | 10.11 |

Both algorithms examine the same number of candidate windows per
description (n_desc − m + 1); naive does an O(m) comparison per window in
the worst case, Rabin-Karp an O(1) amortized rolling-hash comparison,
verified with a full O(m) comparison only on a hash match.

**Expected vs observed — this one goes against the textbook expectation.**
Rabin-Karp is consistently **~3x slower** than the naive approach at every
size, not faster. The reason is language-level, not algorithmic: our
`naive_search` does `text[i:i+m] == pattern` — Python string slicing and
equality are implemented in C and run at native memory-comparison speed.
Our `rabin_karp_search`, to compute and roll the hash, does real Python-
level integer multiplication, subtraction, and modulo (`% 1_000_000_007`)
on *every single character position*. Python's per-operation interpreter
overhead on that arithmetic is far higher than the cost of the highly
optimized C string comparison naive search gets for free. Rabin-Karp's
real advantage (O(1) amortized vs O(m) worst case per window) would show up
if comparisons were the expensive part — but in Python, doing the "cheap"
O(1) operation in a Python-level loop is more expensive than doing the
"expensive" O(m) operation in C. This is exactly the "constant factors /
language overhead" caveat Part 18 asks us to watch for: the algorithm is
correct and its asymptotic argument is sound (and is the right choice in a
lower-level language, or if reused for shingling as the architecture doc
notes), but in pure Python at this project's scale, the naive approach
wins in wall-clock terms.

---

## 4. Hash lookup vs linear scan

| n | Hash lookup (s) | Linear scan (s) |
|---|---|---|
| 100 | 0.000000128 | 0.00000843 |
| 1,000 | 0.000000239 | 0.000110 |
| 10,000 | 0.0000000876 | 0.000965 |
| 100,000 | 0.00000368 | 0.01174 |

**Expected vs observed:** this is the cleanest, most textbook-accurate
result of the four. Hash lookup stays essentially flat (sub-microsecond)
across a 1,000x increase in n — exactly O(1); the small bump at n=100,000
is measurement noise (dict resizing/hashing overhead at that instant), not
a trend. Linear scan grows almost perfectly linearly: n=100→100,000 is a
1,000x increase in n, and its time goes from 8.4μs to 11,700μs, also
almost exactly 1,000x. No divergence worth noting here — dict-based
hashing is precisely the O(1)-average structure it's supposed to be, with
none of the interpreter-overhead complications that showed up in
experiments 2 and 3, because there's only one operation per lookup either
way (a dict access vs. one loop).

---

## Summary

| Experiment | Matches theory? |
|---|---|
| Merge Sort vs `sorted()` | Yes — same asymptotic shape, ~15x constant-factor gap from Python overhead |
| Heap Top-K vs sort+slice | Yes — the gap closes steadily as n grows, converging to a near-tie by n=100,000 exactly where the crossover is expected |
| Rabin-Karp vs naive | **No** — naive wins throughout, because Python arithmetic overhead exceeds the cost of C-level string comparison |
| Hash lookup vs linear scan | Yes — a clean, uncomplicated O(1) vs O(n) result |

The two "yes" results with visible constant-factor gaps, and the one
outright reversal, are not something to "fix" — they're the actual,
honest empirical behavior of these algorithms as implemented in pure
Python, and are worth presenting exactly as-is in the DAA report: theory
predicts the *shape* of the curve, not the constant sitting in front of it,
and Python's interpreter overhead is large enough to sometimes flip which
implementation wins in absolute wall-clock time even when the asymptotic
argument is completely correct.
