# Dynamic News Feed

A news feed application built as a Design and Analysis of Algorithms (DAA)
college project. It's a working news aggregator — articles get ingested,
cleaned, deduplicated, and ranked into a personalized, diverse, explainable
feed — but the actual point of the project is the ranking engine underneath
it: every hand-written algorithm exists because the app genuinely needs it,
not as decoration bolted onto a CRUD app.

---

## 1. Overview

Users get a feed of news articles ranked by a transparent, weighted formula
(interest match, recency, popularity, keyword relevance, diversity
penalty), personalized by their own like/save/dislike/read history, with a
"why am I seeing this?" breakdown on every card. The feed changes visibly
both when new articles arrive and when the user's behavior changes their
preferences — and that dynamic loop is the single most important thing
this project demonstrates and tests for.

## 2. Problem Statement

A plain reverse-chronological news feed shows every user the same thing
and never improves. Building a feed that's personalized, deduplicated,
diverse, and explainable — cheaply, without an ML stack — requires a
specific set of classical algorithms and data structures, each solving one
concrete problem the app breaks without. This project builds and
benchmarks that full pipeline.

## 3. Objectives

- Ingest real top headlines from NewsAPI.org (or a bundled sample
  dataset) through one shared normalize → categorize → dedupe → store
  pipeline.
- Rank articles for each user using a transparent, explainable formula —
  never a black-box model.
- Detect exact and near-duplicate articles.
- Support fast search-as-you-type autocomplete and substring search.
- Surface trending topics and related articles.
- Make the feed visibly dynamic: new articles and new user interactions
  both change what's shown, immediately.
- Implement every core algorithm by hand, benchmark it against a
  library/naive baseline, and document where theory and practice diverge.

## 4. Features

- **Feeds:** For You (personalized), Latest (recency-only), Category
  (personalized within one category).
- **Search:** substring search across titles/descriptions, live
  autocomplete suggestions.
- **Trending:** top topics by recent mentions, recency, and engagement.
- **Related articles:** on every article, via a shared-category/topic
  graph with a same-category Jaccard-similarity fallback.
- **Personalization:** like / dislike / save / mark-read, each nudging the
  relevant category's preference weight; a manual preferences editor too.
- **Bookmarks & history.**
- **Score transparency:** every ranked card shows its score breakdown.
- **Live news from NewsAPI.org:** top headlines across 7 sections,
  auto-categorized and topic-tagged, refreshed in the background every
  few hours (configurable) and on demand.
- **Same story, one card:** near-duplicate stories from different outlets
  are merged at ingestion; the article page lists the other outlets under
  "Also covered by", and wide coverage boosts the story's popularity.
- **Graceful degradation:** live → stored articles → sample data, never
  an error page. A source badge in the masthead ("Live", "Stored",
  "Sample data") and a plain-language notice explain any fallback.
- **API-quota protection:** a per-day request budget and a refresh
  cooldown keep the free NewsAPI plan from being rate-limited.
- **Mock/live mode toggle** (the Live side is disabled, with a hint, when
  no API key is configured).
- **Dynamic-feed indicators:** "N new articles added" and "last updated
  Xs ago" after every refresh, plus a "New stories available" prompt when
  a background refresh lands while you're reading.

## 5. Architecture

```
NewsAPI / Mock JSON → Ingestion → Normalize → Categorize + Tag topics
   → Exact + near-duplicate check → SQLite
   → Feed Engine (Ranking → Heap Top-K → Greedy Diversify)
   → FastAPI → React UI → User Interactions
   → Preference Engine → loops back into the Feed Engine
```

Backend: FastAPI + SQLAlchemy + SQLite. Frontend: React + Vite + Tailwind
CSS, talking to the backend purely over HTTP (`frontend/src/api/client.js`
is the only place that knows the backend exists — no backend code is ever
imported). Full diagrams and the actual dependency graph:
**[docs/architecture.md](docs/architecture.md)**.

> An earlier Streamlit/Python frontend (Phase 7 of the original build) is
> preserved for reference at `frontend-streamlit-legacy/` — it still works
> against the same backend, but the React frontend in `frontend/` is what's
> actively developed and documented from here on.

## 6. Data Flow

| Step | Module |
|---|---|
| Fetch live headlines | `backend/services/news_api_client.py` |
| Ingest (mock or live) + fallback chain | `backend/services/ingestion.py` |
| Background refresh | `backend/services/scheduler.py` |
| Normalize | `backend/services/normalizer.py` |
| Categorize + tag topics | `backend/algorithms/classification.py` |
| Exact-duplicate check | inline in `ingestion.py`, keyed on `content_hash` |
| Near-duplicate merge | `algorithms/deduplication.py` → `is_duplicate_of` |
| Store | `backend/database/repository.py` |
| Feed generation | `backend/services/feed_service.py` → `algorithms/{ranking,heap,diversification}.py` |
| API | `backend/api/routes/*.py` |
| Frontend render | `frontend/src/pages/*.jsx` |
| User interaction | `POST /interactions` → `interaction_service.py` → `preference_engine.py` |
| Loop | next `GET /feed` call re-scores with the updated preferences |

Full request-by-request sequence diagrams: **[docs/architecture.md](docs/architecture.md)**.

## 7. Algorithms Used

| Algorithm | Module | Role |
|---|---|---|
| Hashing (dict-based indexes) | `hashing.py` | O(1) article/content_hash lookups |
| Rabin-Karp | `string_matching.py` | substring search |
| Trie | `trie.py` | search autocomplete |
| Binary heap (hand-written) | `heap.py` | Top-K feed & trending selection |
| Merge sort (hand-written) | `merge_sort.py` | explicit sort utility + benchmark baseline |
| Jaccard similarity (+ sliding time window) | `deduplication.py` | near-duplicate detection and merging |
| Keyword-set classification | `classification.py` | categorizing live "general" headlines |
| Frequency-scored phrase extraction | `classification.py` | topic tags for live articles |
| Graph + BFS | `graph.py` | related articles |
| Greedy diversification | `diversification.py` | feed category diversity |
| Weighted scoring + exponential decay | `ranking.py` | the core ranking formula |
| HashMap counting + heap | `trending.py` | trending topics |

Purpose, pseudocode, and complexity for every one:
**[docs/algorithms.md](docs/algorithms.md)**.

## 8. Data Structures Used

- **Hash table** (Python `dict`) — every O(1) lookup in the app: article-
  by-hash, category preference maps, topic frequency counts.
- **Hash set** — content_hash membership for exact-duplicate checks.
- **Trie** — prefix tree for autocomplete.
- **Binary heap** (array-based, hand-written) — Top-K selection.
- **Graph** (adjacency list) — related-article traversal via BFS.
- **Doubly-nested dict / composite-key rows** — `user_preferences`'s
  `(user_id, category_id, topic_id)` composite primary key.

## 9. Complexity Analysis

| Operation | Complexity |
|---|---|
| Hash lookup / insert | O(1) average |
| Rabin-Karp search | O(n+m) average, O(nm) worst case |
| Trie insert / prefix search | O(m) descend + O(k) collect |
| Heap push/pop | O(log n) |
| Heap Top-K selection | O(n log k) |
| Merge sort | O(n log n) time, O(n) space |
| Jaccard similarity | O(\|A\|+\|B\|) |
| Graph BFS | O(V+E) |
| Greedy diversification | O(n) |
| Ranking a candidate | O(1) |
| Trending computation | O(n) build + O(n log k) select |

Empirically measured (not just theoretical) at n up to 100,000 synthetic
articles: **[docs/benchmarking.md](docs/benchmarking.md)**.

## 10. Database Design

SQLite, 8 tables (`users`, `categories`, `articles`, `topics`,
`article_topics`, `user_preferences`, `user_interactions`, `bookmarks`).
Full field-level schema, indexes, and the exact corrections made from the
original design draft: **[docs/database.md](docs/database.md)**.

## 11. API Docs

FastAPI auto-generates interactive docs at **http://127.0.0.1:8000/docs**
once the backend is running. Full endpoint reference (14 endpoints):
**[docs/api.md](docs/api.md)**.

| Method | Path | Purpose |
|---|---|---|
| GET | `/categories` | list categories |
| GET | `/articles`, `/articles/{id}` | browse / detail |
| GET | `/recommendations/{id}` | related articles |
| GET | `/feed` | the main ranked feed |
| GET | `/search`, `/search/suggest` | search + autocomplete |
| GET | `/trending` | trending topics |
| POST | `/interactions` | record read/like/save/dislike |
| POST/GET | `/bookmarks` | save / list saved articles |
| GET | `/history` | read history |
| GET/PUT | `/preferences` | view / manually edit preferences |
| POST | `/refresh` | pull new articles (reports which source was used) |
| GET | `/status` | data-source health: live/cached/sample, API quota |

## 12. UI 

An editorial identity ("The Signal"), not a dashboard: a serif masthead
(Fraunces) over a horizontal section nav (For You, Latest, Trending,
Categories, Search, Saved, History, Preferences), warm ivory paper with an
oxblood signature accent, no icons-as-decoration and no emoji anywhere.

- **Home / For You** — a mock/live mode toggle and a Refresh feed button
  in the masthead; the main column shows ranked article cards (image,
  category eyebrow, serif headline, byline, description, and plain-text
  actions: Like, Not interested, Save, Mark read), each with a collapsed
  "Why this is here" score breakdown and a lazily-loaded "Related
  articles" disclosure, plus a "Trending now" rail alongside it.
- **Search** — a pill-shaped search field with live autocomplete
  suggestions rendered as tags below it, and matching article cards
  underneath as you type.
- **Preferences** — one slider per category (0–1), live-loaded from
  `GET /preferences`, saved back via `PUT /preferences`.
- **Refresh** — clicking "Refresh feed" shows "+N new · Xs ago" in the
  masthead, ticking up in real time.

(These are exact descriptions of the actual running app, verified during
manual browser testing — not aspirational mockups.)

## 13. Setup

Requirements: Python 3.11+ (developed and tested against 3.14; see the
note in `requirements.txt` about version pins if you're on an older
Python and hit wheel-build errors) and Node.js 18+.

Backend:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

Generate the mock dataset and the database:

```bash
python generate_mock_data.py
python -m backend.database.init_db
python -m backend.database.seed
```

Frontend:

```bash
cd frontend
npm install
```

## 14. Environment Variables

Copy `.env.example` to `.env` to customize (all settings have safe
defaults — **the app runs fully in mock mode with no `.env` file at all**):

| Variable | Default | Purpose |
|---|---|---|
| `NEWS_API_KEY` | *(empty)* | leave blank for mock mode |
| `NEWS_API_URL` | `https://newsapi.org/v2` | live source endpoint |
| `NEWS_API_COUNTRY` | `us` | country for top headlines |
| `NEWS_API_PAGE_SIZE` | `40` | articles requested per section |
| `NEWS_API_DAILY_BUDGET` | `90` | max NewsAPI requests per UTC day |
| `REFRESH_COOLDOWN_SECONDS` | `300` | min gap between live fetches |
| `AUTO_REFRESH_MINUTES` | `180` | background refresh interval in live mode (0 = off) |
| `DATABASE_URL` | `sqlite:///./data/news.db` | SQLAlchemy connection string |
| `APP_ENV` | `mock` | `mock` or `live` |
| `BACKEND_HOST` / `BACKEND_PORT` | `127.0.0.1` / `8000` | FastAPI |

The frontend needs no environment variables in dev — Vite's dev server
proxies `/api/*` straight to the backend (see `frontend/vite.config.js`),
so the browser never needs CORS. For a production build served from a
different origin, set `VITE_API_BASE` to the backend's full URL.

## 15. Running the Project

Two processes, in separate terminals:

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** for the app, **http://127.0.0.1:8000/docs**
for the interactive API reference.

To pull "new" articles at any point: click **Refresh feed** in the
masthead, or `curl -X POST http://127.0.0.1:8000/refresh`.

### Live news

1. Get a free key at https://newsapi.org/register.
2. Copy `.env.example` to `.env` and set `NEWS_API_KEY=<your key>` and
   `APP_ENV=live`.
3. Restart the backend. It fetches headlines on startup and every
   `AUTO_REFRESH_MINUTES`; the UI starts on **Live** and the masthead
   badge shows where the stories came from.

Or ingest once from the command line: `python -m backend.services.ingestion --mode live`.

The free NewsAPI developer plan is for development use only and allows
100 requests/day. One refresh costs 7 requests (one per section), which is
why the daily budget and cooldown exist. Headlines are credited to
NewsAPI.org in the footer, and every story links to its publisher.

**Upgrading an existing database** (created before live ingestion
categorized and merged stories): run `python -m backend.services.maintenance`
once. It backfills missing categories and topics and merges duplicate
stories. Running it again is safe.

## 16. Running Tests

```bash
pytest tests/ -v
```

196 tests (unit + integration), covering every algorithm module, every API
endpoint and its documented error cases, the full ingestion pipeline, the
live NewsAPI path against a fake API (success, partial failure, invalid
key, request budget, cooldown, cache/mock fallback), and
the edge-case checklist (empty DB, single article, near-duplicates,
malformed API responses, 10,000+ synthetic articles, and more — see
`tests/integration/test_edge_cases.py`).

## 17. Benchmarking

```bash
python -m benchmarks.run_benchmarks
```

Runs 4 comparisons (Merge Sort vs `sorted()`, Heap Top-K vs sort-then-
slice, Rabin-Karp vs naive search, hash lookup vs linear scan) at
n ∈ {100, 1,000, 10,000, 100,000}, writing CSVs and charts to
`benchmarks/results/`.

## 18. Results

Full expected-vs-observed analysis, including two genuinely interesting
divergences from naive theoretical expectations (Rabin-Karp losing to
naive search in pure Python, and the heap/sort crossover point), is in
**[docs/benchmarking.md](docs/benchmarking.md)**. Headline numbers:

- Hash lookup stays flat (~0.1μs) from n=100 to n=100,000; linear scan
  grows almost exactly linearly (8.4μs → 11.7ms) — the cleanest O(1) vs
  O(n) result of the four.
- Heap Top-K closes the gap with full-sort-then-slice steadily as n
  grows, landing within ~3% of it by n=100,000 — right where the
  crossover is expected.
- Rabin-Karp is consistently slower than naive substring search in this
  pure-Python implementation, because Python-level rolling-hash
  arithmetic costs more than the C-level string comparison naive search
  gets for free — a real, documented finding, not a bug.

## 19. Limitations

- No authentication — a single hardcoded demo user (`id=1`), by design
  (see the architecture doc's Part 12).
- Live mode's success path is tested against a fake NewsAPI that returns
  NewsAPI-shaped responses. Against the real API, only the error path has
  been exercised (an invalid key is rejected after one request).
- Category classification and topic extraction are keyword heuristics.
  They're explainable and fast, but they'll mislabel some "general"
  headlines (those with no keyword match show as "General").
- Refresh state (last source, daily request count) is kept in memory, so
  it resets when the backend restarts. The stored articles persist.
- The bundled sample dataset has fixed September 2026 dates. When nothing
  falls inside a recent window, pages widen the window instead of
  rendering empty, so sample-mode recency scores are near zero.
- Recommendation/graph/trie structures are rebuilt fresh on each request
  rather than cached or updated incrementally — fine at this project's
  data scale, not something to do at real scale.
- Search ranking is a plain substring match; it isn't blended with the
  personalization ranking formula (the architecture doc notes this
  blending as optional).

## 20. Future Improvements

- Persist refresh state and the API request counter (e.g. a small
  `fetch_log` table) so they survive restarts.
- Additional live sources (RSS via the already-installed `feedparser`)
  feeding the same pipeline.
- Incremental index updates (Trie/graph/topic-index) instead of full
  rebuilds per request.
- Topic-level preferences (the schema already supports them via
  `user_preferences.topic_id`; only category-level preferences are wired
  up today).
- A real onboarding flow (interest selection) instead of everyone
  starting at the cold-start baseline.
- Caching layer for `/trending` and `/recommendations` if this ever needed
  to handle real traffic.
- A CI pipeline running `pytest` and the benchmark suite on every change.

---

## Project Structure

```
dynamic-news-feed/
├── backend/
│   ├── main.py               # FastAPI entrypoint — no business logic
│   ├── config.py              # env-var settings
│   ├── api/                   # routes/, errors.py, serializers.py
│   ├── services/               # orchestration (ingestion, feed, preferences, search, ...)
│   ├── algorithms/              # pure, dependency-free algorithm implementations
│   ├── models/                  # SQLAlchemy models (schema only)
│   ├── database/                 # engine, repository.py, init_db.py, seed.py
│   └── utils/                     # text cleaning, date parsing
├── frontend/                       # React + Vite + Tailwind CSS
│   ├── index.html
│   ├── vite.config.js               # dev-server proxy to the backend
│   └── src/
│       ├── main.jsx, App.jsx          # entrypoint + router
│       ├── api/client.js               # HTTP-only bridge to the backend
│       ├── lib/                         # AppContext, useApi hook, formatting
│       ├── pages/                        # one file per screen
│       └── components/                    # Layout, ArticleCard, ScoreBreakdown, ...
├── frontend-streamlit-legacy/       # the original Phase 7 frontend (reference only)
├── data/mock_articles.json      # generated by generate_mock_data.py
├── tests/{unit,integration}/     # 196 tests (backend)
├── benchmarks/run_benchmarks.py + results/
├── docs/                          # architecture, algorithms, database, api,
│                                  # development-rules, benchmarking
├── requirements.txt
├── AGENTS.md                      # development protocol (mirrored in docs/development-rules.md)
└── .env.example
```
