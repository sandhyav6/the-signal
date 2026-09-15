"""benchmarks/run_benchmarks.py — Phase 9 performance benchmarks (Part 18
of the architecture doc).

Compares, at n in {100, 1000, 10000, 100000} (synthetic data — no live API
calls), averaged over 5 runs each:
  1. Merge Sort vs Python's sorted() — fully sorting n articles by score.
  2. Heap Top-K vs full-sort-then-slice — selecting the top 20 of n.
  3. Rabin-Karp vs naive substring search — a pattern across n descriptions.
  4. Hash lookup vs linear scan — finding one article by hash among n.

Writes one CSV + one PNG line chart (log-scale x-axis) per experiment into
benchmarks/results/, and prints a summary table to stdout. See
docs/benchmarking.md for the expected-vs-observed complexity discussion.

Run:
    python -m benchmarks.run_benchmarks
"""

import csv
import math
import os
import random
import time
from typing import Callable

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from backend.algorithms.heap import top_k
from backend.algorithms.merge_sort import merge_sort
from backend.algorithms.string_matching import naive_search, rabin_karp_search

SIZES = [100, 1_000, 10_000, 100_000]
REPEATS = 5
TOP_K = 20

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

_WORD_POOL = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "market",
    "election", "storm", "breakthrough", "scientists", "government", "ai",
    "economy", "championship", "vaccine", "startup", "climate",
]

random.seed(42)


def _make_articles(n: int) -> list[dict]:
    """Synthetic articles: id, content_hash, score, description.

    Complexity: O(n).
    """
    return [
        {
            "id": i,
            "content_hash": f"hash-{i:08d}",
            "score": random.random() * 100,
            "description": " ".join(random.choice(_WORD_POOL) for _ in range(40)),
        }
        for i in range(n)
    ]


def _time_avg(fn: Callable[[], None], repeats: int = REPEATS) -> float:
    """Average wall-clock seconds of `fn()` over `repeats` calls."""
    total = 0.0
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        total += time.perf_counter() - start
    return total / repeats


def _write_csv(name: str, rows: list[dict]) -> str:
    """Write `rows` (list of flat dicts, same keys) as a CSV file."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, f"{name}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def _plot(name: str, rows: list[dict], series: list[tuple[str, str]], title: str, ylabel: str) -> str:
    """Save a log-x-scale line chart with one line per (column, label) pair."""
    plt.figure(figsize=(7, 5))
    ns = [r["n"] for r in rows]
    for column, label in series:
        plt.plot(ns, [r[column] for r in rows], marker="o", label=label)
    plt.xscale("log")
    plt.xlabel("n (number of articles)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.5)
    path = os.path.join(RESULTS_DIR, f"{name}.png")
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


def benchmark_merge_sort_vs_sorted() -> list[dict]:
    """Time to fully sort n articles by score, descending.

    Also records the theoretical O(n log n) operation count for merge sort
    as a reference column (Part 18: "count operations where meaningful").
    """
    rows = []
    for n in SIZES:
        articles = _make_articles(n)
        merge_time = _time_avg(lambda: merge_sort(articles, key=lambda a: a["score"], reverse=True))
        sorted_time = _time_avg(lambda: sorted(articles, key=lambda a: a["score"], reverse=True))
        rows.append({
            "n": n,
            "merge_sort_seconds": merge_time,
            "sorted_seconds": sorted_time,
            "expected_merge_sort_ops_n_log_n": n * math.log2(max(n, 2)),
        })
        print(f"[merge_sort vs sorted]      n={n:>7}: merge_sort={merge_time:.6f}s  sorted()={sorted_time:.6f}s")
    return rows


def benchmark_heap_topk_vs_sort_slice() -> list[dict]:
    """Time to select the top TOP_K of n articles by score.

    Records theoretical O(n log k) (heap) vs O(n log n) (full sort)
    operation counts alongside the observed timing.
    """
    rows = []
    for n in SIZES:
        articles = _make_articles(n)
        heap_time = _time_avg(lambda: top_k(articles, TOP_K, key=lambda a: a["score"]))
        sort_slice_time = _time_avg(lambda: sorted(articles, key=lambda a: a["score"], reverse=True)[:TOP_K])
        rows.append({
            "n": n,
            "heap_topk_seconds": heap_time,
            "sort_then_slice_seconds": sort_slice_time,
            "expected_heap_ops_n_log_k": n * math.log2(max(TOP_K, 2)),
            "expected_sort_ops_n_log_n": n * math.log2(max(n, 2)),
        })
        print(f"[heap top-k vs sort+slice]  n={n:>7}: heap={heap_time:.6f}s  sort+slice={sort_slice_time:.6f}s")
    return rows


def benchmark_string_matching() -> list[dict]:
    """Time to search for one pattern across n article descriptions.

    Both algorithms examine the same (n-m+1) candidate windows per
    description; naive does O(m) work per window worst case, Rabin-Karp
    O(1) amortized (a rolling hash compare, verified only on a hash hit).
    """
    pattern = "breakthrough"
    rows = []
    for n in SIZES:
        articles = _make_articles(n)
        descriptions = [a["description"] for a in articles]

        def _search_all(fn):
            for text in descriptions:
                fn(text, pattern)

        rk_time = _time_avg(lambda: _search_all(rabin_karp_search))
        naive_time = _time_avg(lambda: _search_all(naive_search))
        rows.append({"n": n, "rabin_karp_seconds": rk_time, "naive_seconds": naive_time})
        print(f"[Rabin-Karp vs naive]       n={n:>7}: rabin_karp={rk_time:.6f}s  naive={naive_time:.6f}s")
    return rows


def benchmark_hash_vs_linear_scan() -> list[dict]:
    """Time to find one article by content_hash among n, dict vs list scan.

    Each timed call repeats the same lookup `lookups_per_run` times (a
    single O(1) dict lookup is too fast to time reliably on its own).
    """
    lookups_per_run = 200
    rows = []
    for n in SIZES:
        articles = _make_articles(n)
        index = {a["content_hash"]: a for a in articles}
        target_hash = articles[n // 2]["content_hash"]  # an average-case (middle) target

        def _hash_lookup():
            for _ in range(lookups_per_run):
                _ = index[target_hash]

        def _linear_scan():
            for _ in range(lookups_per_run):
                for a in articles:
                    if a["content_hash"] == target_hash:
                        break

        hash_time = _time_avg(_hash_lookup) / lookups_per_run
        linear_time = _time_avg(_linear_scan) / lookups_per_run
        rows.append({"n": n, "hash_lookup_seconds": hash_time, "linear_scan_seconds": linear_time})
        print(f"[hash lookup vs linear]     n={n:>7}: hash={hash_time:.8f}s  linear={linear_time:.8f}s")
    return rows


def _run_experiment(
    label: str,
    name: str,
    benchmark_fn: Callable[[], list[dict]],
    series: list[tuple[str, str]],
    title: str,
) -> None:
    """Run one experiment and write its CSV + chart outputs."""
    print(f"=== {label} ===")
    rows = benchmark_fn()
    _write_csv(name, rows)
    _plot(name, rows, series, title, "seconds")


def main() -> None:
    """Run all four experiments and write their CSV + chart outputs."""
    os.makedirs(RESULTS_DIR, exist_ok=True)

    _run_experiment(
        "1. Merge Sort vs sorted()", "merge_sort_vs_sorted", benchmark_merge_sort_vs_sorted,
        [("merge_sort_seconds", "Merge Sort (hand-written)"), ("sorted_seconds", "sorted() (Timsort)")],
        "Merge Sort vs sorted() — full sort by score",
    )
    _run_experiment(
        "2. Heap Top-K vs full-sort-then-slice", "heap_topk_vs_sort_slice", benchmark_heap_topk_vs_sort_slice,
        [("heap_topk_seconds", "Heap Top-K"), ("sort_then_slice_seconds", "sorted()[:20]")],
        f"Heap Top-{TOP_K} vs full-sort-then-slice",
    )
    _run_experiment(
        "3. Rabin-Karp vs naive substring search", "string_matching", benchmark_string_matching,
        [("rabin_karp_seconds", "Rabin-Karp"), ("naive_seconds", "Naive search")],
        "Rabin-Karp vs naive search — pattern across n descriptions",
    )
    _run_experiment(
        "4. Hash lookup vs linear scan", "hash_vs_linear_scan", benchmark_hash_vs_linear_scan,
        [("hash_lookup_seconds", "Hash lookup (dict)"), ("linear_scan_seconds", "Linear scan")],
        "Hash lookup vs linear scan — find one article by hash",
    )

    print(f"\nAll results written to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
