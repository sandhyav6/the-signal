# The Signal

**Live site: [the-signal-nze8.onrender.com](https://the-signal-nze8.onrender.com)**

The Signal is a news feed that learns what you like and tells you why it
showed you each story. It pulls real headlines from NewsAPI.org every few
hours, removes repeats, sorts the rest by how relevant they are to you, and
puts a short "why this is here" breakdown under every article.

I built it for understanding the algorithms that can be used and implemented. The news
app is the visible part. The real subject is the ranking engine behind it,
where every algorithm is written by hand and is there because the feed
needs it.

> The site runs on Render's free plan. If nobody has visited for a while,
> the first load can take up to a minute while the server wakes up.

---

## What you can do on the site

- **For You:** your personal feed. Like a story, mark it "Not interested",
  save it or mark it read, and the next load of the feed shifts toward
  what you engage with.
- **Why this is here:** open this under any story to see its score and
  the five parts it was built from (your interest in the category, how
  recent it is, how popular it is, search relevance, and a penalty for
  showing too much of one category).
- **Latest:** newest stories first, no personalisation.
- **Trending:** topics getting the most coverage and engagement right now.
- **Categories:** Technology, Science, Politics, Business, Sports, Health
  and Entertainment.
- **Search:** suggestions appear while you type, and results update as
  you go.
- **Related stories and "Also covered by":** each article page lists
  similar stories and the other outlets that reported the same story.
- **Saved, History and Preferences:** your bookmarks, what you've read,
  and sliders to set how much you care about each category.

The badge at the top tells you where the stories came from: **Live**
(fresh from NewsAPI), **Stored** (articles already saved, used when the
live source is briefly unavailable) or **Sample data** (a built-in demo
set, used only when there is nothing else).

---

## How it works, in plain terms

1. **Collect.** Every few hours the server asks NewsAPI for the top
   headlines in each section.
2. **Clean up.** It throws away broken entries, strips the publisher's
   name off the end of headlines ("... - Reuters"), and works out a
   category and a few topic tags for each story.
3. **Remove repeats.** The same story often arrives from five outlets.
   Exact copies are dropped. Close copies are kept but grouped under the
   first one, so you see the story once, and a story covered by many
   outlets gets a small popularity boost.
4. **Rank.** For each visit, every recent story gets a score. The best ones
   are picked and then shuffled slightly so one category can't take over
   the whole page.
5. **Learn.** Your likes, saves and dislikes adjust your category weights,
   and the next feed is scored with the new weights.

If NewsAPI is down, the key is wrong or the daily request limit is used up,
the site keeps working with the articles it already has. It never shows an
error page because of the news source.

---

## Under the hood

```
NewsAPI (or sample JSON)
  -> ingestion: normalize, categorize, tag topics
  -> exact + near-duplicate check -> SQLite
  -> feed engine: score every candidate -> heap Top-K -> greedy diversify
  -> FastAPI (/api) -> React UI
  -> user interactions -> preference engine -> back into the feed engine
```

**Stack:** Python 3.14, FastAPI, SQLAlchemy and SQLite on the backend.
React 19, Vite and Tailwind CSS on the frontend. In production, one Docker
container serves both the built frontend and the API from the same URL.

The ranking formula, with every term scaled to 0 to 100:

```
score = 0.35 * interest + 0.25 * recency + 0.20 * popularity
      + 0.15 * keyword_relevance - 0.05 * repetition_penalty

recency = 100 * e^(-λ * age_in_hours),  λ = ln 2 / 24   (halves every 24 hours)
```

The same function returns the score and its breakdown, so what the
"why this is here" panel shows is always exactly what was used to rank.

### Algorithms

| Algorithm | File (`backend/algorithms/`) | What it does in the app |
|---|---|---|
| Hash tables and hash sets | `hashing.py` | O(1) lookups by id and content hash |
| Rabin-Karp | `string_matching.py` | substring search |
| Trie | `trie.py` | search-as-you-type suggestions |
| Binary heap (hand-written) | `heap.py` | picks the top K stories and topics |
| Merge sort (hand-written) | `merge_sort.py` | sorting utility and benchmark baseline |
| Jaccard similarity with a time window | `deduplication.py` | finds and groups near-duplicate stories |
| Keyword-set classification | `classification.py` | assigns a category to uncategorised headlines |
| Frequency-scored phrase extraction | `classification.py` | topic tags such as "federal reserve" |
| Graph + BFS | `graph.py` | related stories |
| Greedy diversification | `diversification.py` | caps how many stories one category gets per page |
| Weighted scoring with exponential decay | `ranking.py` | the ranking formula above |
| Hash map counting + heap | `trending.py` | trending topics |

Pseudocode and reasoning for each one are in
[docs/algorithms.md](docs/algorithms.md).

### Complexity

| Operation | Complexity |
|---|---|
| Hash lookup / insert | O(1) average |
| Rabin-Karp search | O(n + m) average, O(nm) worst case |
| Trie insert / prefix search | O(m) to descend + O(k) to collect |
| Heap push / pop | O(log n) |
| Heap Top-K selection | O(n log k) |
| Merge sort | O(n log n) time, O(n) space |
| Jaccard similarity | O(\|A\| + \|B\|) |
| Batch near-duplicate linking | O(n log n) sort + O(n * w), w = stories inside one 48 h window |
| Graph BFS | O(V + E) |
| Greedy diversification | O(n) |
| Scoring one article | O(1) |
| Trending | O(n) to count + O(n log k) to select |

### Benchmark results

`python -m benchmarks.run_benchmarks` compares the hand-written versions
with a library or naive baseline at n = 100, 1,000, 10,000 and 100,000.
Full write-up in [docs/benchmarking.md](docs/benchmarking.md).

- Hash lookup stays flat at about 0.1 μs across all sizes, while a linear
  scan grows from 8.4 μs to 11.7 ms. The clearest O(1) vs O(n) result.
- Heap Top-K gets closer to sort-then-slice as n grows and is within about
  3% of it at n = 100,000, which is roughly where theory says the two
  should cross.
- Rabin-Karp is slower than naive substring search here. In pure Python,
  the rolling-hash arithmetic costs more than the C-level string comparison
  the naive version gets for free. That's a real finding, not a bug.

### Data source and fallbacks

- One refresh makes 7 NewsAPI requests: one each for technology, science,
  business, sports, health and entertainment, plus "general". Politics
  isn't a NewsAPI category, so general headlines are categorised by
  keyword.
- A daily request budget (90 by default, under the free plan's 100) and a
  5-minute cooldown between refreshes protect the API key.
- The key is sent in a request header, never in the URL, so it can't end
  up in logs.
- Order of fallback: live headlines, then stored articles, then the
  sample dataset. `/api/refresh` and `/api/status` report which one was
  used.

### Database

SQLite with 8 tables: `users`, `categories`, `articles`, `topics`,
`article_topics`, `user_preferences`, `user_interactions` and `bookmarks`.
Duplicate stories point at their original through
`articles.is_duplicate_of`. Full schema in
[docs/database.md](docs/database.md).

---

## Running it on your own computer

You need Python 3.11 or newer (developed on 3.14) and Node.js 18 or newer.

**1. Backend**

```bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
```

**2. Database with sample articles**

```bash
python -m backend.database.seed
```

**3. Frontend**

```bash
cd frontend
npm install
```

**4. Start both** (two terminals)

```bash
uvicorn backend.main:app --reload
```

```bash
cd frontend
npm run dev
```

Open http://localhost:5173 for the app and http://127.0.0.1:8000/docs for
the interactive API docs.

### Turning on live news

1. Get a free key at https://newsapi.org/register.
2. Copy `.env.example` to `.env`, then set `NEWS_API_KEY=your-key` and
   `APP_ENV=live`.
3. Restart the backend. It fetches headlines straight away and then every
   3 hours, and the badge switches to **Live**.

Without a `.env` file the app still runs, just on sample data.

If your database was created before live ingestion existed, run
`python -m backend.services.maintenance` once. It fills in missing
categories and topics and groups duplicate stories. It's safe to run
again.

### Settings

All optional. Put them in `.env`.

| Variable | Default | Meaning |
|---|---|---|
| `NEWS_API_KEY` | empty | your NewsAPI key; empty means sample data |
| `APP_ENV` | `mock` | `live` to use NewsAPI |
| `NEWS_API_COUNTRY` | `us` | country for top headlines |
| `NEWS_API_PAGE_SIZE` | `40` | stories requested per section |
| `NEWS_API_DAILY_BUDGET` | `90` | max NewsAPI requests per day (UTC) |
| `REFRESH_COOLDOWN_SECONDS` | `300` | minimum gap between live fetches |
| `AUTO_REFRESH_MINUTES` | `180` | background refresh interval, 0 turns it off |
| `DATABASE_URL` | `sqlite:///./data/news.db` | database location |
| `SERVE_FRONTEND` | `false` | serve the built React app from the backend (set in the Dockerfile) |

---

## Deployment

The live site runs on [Render](https://render.com) from the `Dockerfile`
in this repo. The image builds the React app, installs the backend, and
starts one server that serves the site at `/` and the API at `/api`. On
startup it creates the database tables, categories and default user, so
there are no manual setup steps.

To deploy your own copy:

1. Push the repo to GitHub.
2. In Render, choose **New > Blueprint** and pick the repo. Render reads
   `render.yaml`.
3. Paste your NewsAPI key when it asks for `NEWS_API_KEY`, then deploy.
4. Point a free uptime monitor such as UptimeRobot at `/health` every
   5 minutes. Render's free plan sleeps after 15 idle minutes, and while
   it sleeps the background refresh is paused too.

On the free plan the disk is temporary, so saved articles, history and
preferences reset whenever the service restarts or redeploys. Headlines
come back by themselves on startup.

---

## Tests

```bash
pytest tests/ -v
```

196 unit and integration tests. They cover every algorithm, every API
endpoint and its error cases, and the ingestion pipeline. The live NewsAPI
path is tested against a fake API: success, one section failing, an
invalid key, the daily budget running out, the cooldown, and the fallback
to stored or sample data. Edge cases include an empty database, a single
article, near-duplicates, malformed API responses and 10,000+ articles.

---

## API

Interactive docs are at `/docs` on a running server. Full reference:
[docs/api.md](docs/api.md). On the deployed site every path below starts
with `/api`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/categories` | list categories |
| GET | `/articles`, `/articles/{id}` | browse, or one article with related stories and coverage |
| GET | `/recommendations/{id}` | related stories |
| GET | `/feed` | the ranked feed (`foryou`, `latest` or `category`) |
| GET | `/search`, `/search/suggest` | search and autocomplete |
| GET | `/trending` | trending topics |
| POST | `/interactions` | record a read, like, save or dislike |
| POST / GET | `/bookmarks` | save a story / list saved stories |
| GET | `/history` | reading history |
| GET / PUT | `/preferences` | view or edit category weights |
| POST | `/refresh` | fetch new stories now; says which source was used |
| GET | `/status` | live, stored or sample; API requests used today |
| GET | `/health` | health check for uptime monitors |

---

## Project structure

```
dynamic-news-feed/
├── backend/
│   ├── main.py            app setup, routes, serves the built frontend in production
│   ├── config.py          settings read from environment variables
│   ├── algorithms/        the hand-written algorithms (no database or web code)
│   ├── services/          ingestion, NewsAPI client, feed, search, trending, scheduler
│   ├── api/routes/        one file per group of endpoints
│   ├── database/          engine, repository, seeding
│   ├── models/            SQLAlchemy tables
│   └── utils/             text cleaning and date parsing
├── frontend/              React + Vite + Tailwind
│   └── src/               pages, components, API client
├── frontend-streamlit-legacy/   the first frontend, kept for reference
├── tests/                 unit and integration tests
├── benchmarks/            benchmark runner (results are generated)
├── docs/                  architecture, algorithms, database, API, benchmarks
├── data/mock_articles.json      sample dataset
├── Dockerfile, render.yaml      deployment
└── .env.example           settings template
```

---

## Known limitations

- There are no user accounts. Everyone shares one demo user, so on the
  live site your likes and saves mix with other visitors'.
- Categories and topic tags come from keyword rules. They're fast and easy
  to explain, but some general headlines get no category and show as
  "General".
- The refresh status and the daily request count live in memory and reset
  when the server restarts.
- NewsAPI's free plan is meant for development. A site with real traffic
  would need a paid plan or a different source.
- The trie, graph and topic index are rebuilt on each request. That's fine
  at this size but wouldn't scale to a large archive.
- Search results are ordered by date and aren't blended with the
  personal ranking yet.

## Ideas for later

- User accounts, so each visitor gets their own feed.
- A persistent database on the host, plus storing refresh history.
- More sources, such as publishers' RSS feeds, through the same pipeline.
- Topic-level preferences (the database already supports them).
- Updating the trie and graph incrementally instead of rebuilding them.
- Running the tests automatically on every push.
