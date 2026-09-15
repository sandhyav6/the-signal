# API Reference

FastAPI backend, entrypoint [`backend/main.py`](../backend/main.py). Run it
with `uvicorn backend.main:app --reload` and browse the interactive docs at
**http://127.0.0.1:8000/docs** (Swagger UI, auto-generated from the route
signatures — always the most up-to-date reference; this file is the
narrative version).

Every error response has the shape:
```json
{"error": "plain-language message", "code": "machine_readable_code"}
```
never a raw stack trace or FastAPI's default validation-error list.

There is no login flow — every endpoint operates against a `user_id` you
supply directly, and the seed script always creates exactly one default
user with `id=1`.

---

## GET /categories
List all categories, for nav menus / category chips.
**Response:** `[{"id": 1, "name": "Technology", "slug": "technology"}, ...]`

## GET /articles
Browse all articles, paginated.
**Query params:** `page` (default 1), `limit` (default 20, max 100), `category` (optional category id filter)
**Response:** `{"page", "limit", "total", "articles": [...]}`
**Errors:** `400 bad_pagination` — `page < 1` or `limit` outside `[1, 100]`

## GET /articles/{article_id}
Full article detail plus related articles (graph BFS / Jaccard fallback).
**Response:** `{"article": {...}, "related": [...]}`
**Errors:** `404 article_not_found`

## GET /recommendations/{article_id}
Related articles only (same engine as the `related` field above, as its
own endpoint per the architecture doc's API table).
**Response:** `{"article_id", "related": [...]}`
**Errors:** `404 article_not_found`

## GET /feed
The main feed — ranked, diversified, and explained.
**Query params:**
- `user_id` (required)
- `type`: `foryou` (default, fully personalized) | `latest` (plain recency, no ranking) | `category` (personalized, restricted to one category — requires `category`)
- `category` (required when `type=category`)
- `page` (default 1)

**Response:** `{"user_id", "type", "page", "articles": [{"article", "score", "breakdown"}, ...]}`
(`score`/`breakdown` are `null` for `type=latest`, which has no ranking to explain.)
**Errors:** `400 unknown_feed_type`, `400 missing_category` (type=category with no category param), `404 user_not_found`

## GET /search
Substring search (Rabin-Karp) over article titles/descriptions.
**Query params:** `q` (required, non-empty), `page` (default 1)
**Response:** `{"query", "page", "total", "articles": [...]}`
**Errors:** `400 empty_query`

## GET /search/suggest
Trie-backed autocomplete.
**Query params:** `prefix`
**Response:** `{"prefix", "suggestions": [...]}`

## GET /trending
Top trending topics (HashMap counting + heap Top-K, last 24h by default).
**Query params:** `limit` (default 5)
**Response:** `{"topics": [{"topic", "score"}, ...]}`

## POST /interactions
Record a read/like/save/dislike; updates the article's engagement counters
and the user's category preference weight in one call.
**Body:** `{"user_id": int, "article_id": int, "type": "read"|"like"|"save"|"dislike"}`

> **Naming note:** the JSON field is `type` (matching the architecture
> spec's API table), but the database column it's written to is
> `interaction_type` (see `docs/database.md`) — the route explicitly maps
> one to the other; see `backend/api/routes/interactions.py`.

**Response (201):** `{"user_id", "article_id", "type", "preference_weight"}`
(`preference_weight` is the resulting category weight, or `null` if the
article has no category to personalize against)
**Errors:** `400 invalid_interaction_type`, `404 user_not_found`, `404 article_not_found`

## POST /bookmarks
Save an article.
**Body:** `{"user_id": int, "article_id": int}`
**Response (201):** `{"user_id", "article_id", "created": bool}` (`created=false` if already bookmarked — not an error)
**Errors:** `404 user_not_found`, `404 article_not_found`

## GET /bookmarks
A user's saved articles.
**Query params:** `user_id`
**Response:** `{"user_id", "articles": [...]}`
**Errors:** `404 user_not_found`

## GET /history
Articles a user has marked "read".
**Query params:** `user_id`
**Response:** `{"user_id", "articles": [...]}`
**Errors:** `404 user_not_found`

## GET /preferences
A user's current category preference map.
**Query params:** `user_id`
**Response:** `{"user_id", "preferences": {"<category_id>": weight, ...}}`
**Errors:** `404 user_not_found`

## PUT /preferences
Manually set category weights (as opposed to the interaction-driven deltas
`POST /interactions` applies).
**Body:** `{"user_id": int, "updates": {"<category_id>": weight, ...}}`
(category ids are strings because JSON object keys are always strings)
**Response:** `{"user_id", "preferences": {...}}` (the full updated map)
**Errors:** `400 invalid_category` (unknown or non-integer category id), `400 invalid_weight` (outside [0,1]), `404 user_not_found`

## POST /refresh
Pull new articles through the ingestion pipeline.
**Body (optional):** `{"mode": "mock"|"live"}` — omit or send `{}` to use the server's configured `APP_ENV`
**Response:** `{"added": int, "duplicates_skipped": int}`
**Errors:** none — a live-fetch failure (network error, timeout, or a
malformed/unexpected-shape JSON response) is caught internally and falls
back to mock data; this endpoint always returns 200.

---

## Summary table

| Method | Path | Auth | Notes |
|---|---|---|---|
| GET | /categories | — | |
| GET | /articles | — | paginated |
| GET | /articles/{id} | — | includes related |
| GET | /recommendations/{id} | — | |
| GET | /feed | user_id | foryou / latest / category |
| GET | /search | — | Rabin-Karp |
| GET | /search/suggest | — | Trie |
| GET | /trending | — | HashMap + heap |
| POST | /interactions | user_id (body) | 201 |
| POST | /bookmarks | user_id (body) | 201 |
| GET | /bookmarks | user_id | |
| GET | /history | user_id | |
| GET | /preferences | user_id | |
| PUT | /preferences | user_id (body) | |
| POST | /refresh | — | never 500s |
