# Architecture

## High-level architecture

```
┌────────────┐   ┌───────────┐   ┌──────────────┐   ┌────────────┐
│ Mock JSON /│──▶│ Ingestion │──▶│ Normalize +  │──▶│  SQLite DB │
│ NewsAPI    │   │  Service  │   │ exact-dedupe │   │            │
└────────────┘   └───────────┘   └──────────────┘   └─────┬──────┘
                                                            │
                       ┌────────────────────────────────────────────────┐
                       │            Feed Generation Engine               │◀┘
                       │  Ranking (score+decay) → Heap Top-K → Greedy    │
                       │  Diversification → Explanation objects          │
                       └───────────────────────┬──────────────────────────┘
                                                │
                                       ┌────────▼────────┐
                                       │   FastAPI (API)  │◀── Search (Rabin-Karp/Trie),
                                       └────────┬─────────┘    Trending (HashMap+Heap),
                                                │               Recommendations (Graph+BFS)
                                       ┌────────▼─────────┐
                                       │  React Frontend   │
                                       └────────┬─────────┘
                                                │  interactions (like/save/read)
                                       ┌────────▼─────────┐
                                       │ Preference Engine │──▶ loops back into Feed Engine
                                       └───────────────────┘
```

## Component dependency graph (as built)

```
frontend/          → HTTP only → backend/api/
backend/api/routes → backend/services/, backend/api/{errors,serializers}
backend/services/  → backend/algorithms/, backend/database/
backend/algorithms/ → (nothing else in the project — pure functions)
backend/database/  → backend/models/
```

`algorithms/` has zero internal dependencies (verified by grep in every
phase's report) — every algorithm file is independently importable and
testable with plain Python objects. `frontend/` never imports `backend.*`
directly — its only channel to the app is HTTP (`frontend/api_client.py`).

**Services** (a superset of the architecture doc's original list — three
were added during Phase 6 specifically so route files never call
`algorithms/` or raw SQL directly, keeping the "routes only parse + call
services + serialize" rule intact):
- `ingestion.py`, `normalizer.py` — Phase 2
- `feed_service.py`, `index_manager.py` — Phase 4
- `preference_engine.py` — Phase 5
- `interaction_service.py`, `search_service.py`, `recommendation_service.py`, `trending_service.py` — added in Phase 6

## Database ER (see `docs/database.md` for full field-level detail)

```
users 1───* user_preferences *───1 categories
users 1───* user_preferences *───1 topics       (one axis or the other, per row)
users 1───* user_interactions *───1 articles
users 1───* bookmarks *───1 articles
categories 1───* articles
articles *───* topics  (via article_topics)
articles 0..1───* articles   (is_duplicate_of, self-referential)
```

## Request flow — personalized feed

```
UI → GET /feed?user_id=1&type=foryou
   → feed_service.generate_feed(): load candidate articles (last 7 days)
   → ranking.compute_score() per article using user_preferences
   → heap.top_k(candidates, k=20)
   → diversification.greedy_diversify()
   → serializers.serialize_feed_entry() (attaches explanation breakdowns)
   → JSON → UI renders cards
```

## Request flow — search

```
UI (keystroke) → GET /search/suggest?prefix=ai
               → search_service.suggest() → index_manager.build_trie() → trie.search()
               → suggestion list → UI dropdown

UI (submit)     → GET /search?q=...
               → search_service.search_articles() → rabin_karp_search() per description
               → results → UI
```

## Request flow — new article ingestion

```
POST /refresh → ingestion.ingest() [mock or live; live falls back to mock
                on any network failure OR malformed/unexpected JSON shape]
              → normalizer.normalize() per raw article
              → exact-duplicate check (content_hash) inline in ingest()
              → repository.insert_article() [also de-dupes by url —
                its own was_created flag is the source of truth for
                added vs. duplicate counts, not just the pre-check]
              → response: {added, duplicates_skipped}
```

## Request flow — user interaction

```
UI click Like → POST /interactions {user_id, article_id, type:"like"}
              → interaction_service.record_interaction():
                  1. repository.record_interaction()      — history row
                  2. repository.bump_article_engagement()  — like_count + popularity_score nudge
                  3. preference_engine.apply_interaction_for_article() — user_preferences weight update
              → 201 response {preference_weight}
              → next GET /feed reflects the change immediately
```

This last flow is the project's central "dynamic" claim (architecture doc
Part 10): it's directly proven end-to-end by
`tests/integration/test_interaction_updates_feed.py`.
