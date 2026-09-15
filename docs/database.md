# Database Design

SQLite (`data/news.db`), accessed via SQLAlchemy 2.0. Schema defined in
[`backend/models/models.py`](../backend/models/models.py), created by
`python -m backend.database.init_db`, seeded by `python -m backend.database.seed`.

This reflects the **as-built** schema — several fields differ from the
original architecture draft; see "Deviations from the original design"
at the bottom for exactly what changed and why.

## Tables

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| username | TEXT | UNIQUE, NOT NULL |
| created_at | DATETIME | NOT NULL |

A single default user (`id=1`, `username="default_user"`) is created by the
seed script — this project has no login flow (Part 12 of the architecture
doc: personalization is demonstrated without a full auth system).

### `categories`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | UNIQUE, NOT NULL |
| slug | TEXT | UNIQUE, NOT NULL |

7 fixed categories seeded on startup: Technology, Science, Politics,
Business, Sports, Health, Entertainment.

### `articles`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| title | TEXT | NOT NULL |
| description | TEXT | nullable |
| content | TEXT | nullable |
| url | TEXT | **UNIQUE**, NOT NULL |
| image_url | TEXT | nullable |
| source_name | TEXT | NOT NULL |
| author | TEXT | nullable |
| category_id | INTEGER FK → categories.id | **nullable** — categorization happens after ingestion (Phase 3/4), not at ingestion time |
| content_hash | TEXT | NOT NULL, UNIQUE, indexed — SHA-256 of the normalized title, the exact-duplicate key |
| is_duplicate_of | INTEGER FK → articles.id | nullable — reserved for a future near-duplicate merge step; nothing sets it automatically yet |
| published_at | DATETIME | NOT NULL, indexed |
| popularity_score | FLOAT | default 0.0, nudged by interactions |
| like_count / dislike_count / save_count / read_count | INTEGER | default 0 each |
| fetched_at | DATETIME | NOT NULL, default now |

Indexes: `content_hash`, `published_at`, `category_id`.

### `topics`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| name | TEXT | UNIQUE, NOT NULL |

### `article_topics` (many-to-many junction)
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| article_id | INTEGER FK → articles.id | NOT NULL |
| topic_id | INTEGER FK → topics.id | NOT NULL |

Unique constraint on `(article_id, topic_id)`; indexed on `topic_id`.

### `user_preferences`
| Column | Type | Notes |
|---|---|---|
| user_id | INTEGER FK → users.id | part of composite PK |
| category_id | INTEGER FK → categories.id | part of composite PK, **nullable** |
| topic_id | INTEGER FK → topics.id | part of composite PK, **nullable** |
| weight | FLOAT | default 0.1 (cold-start baseline) |
| updated_at | DATETIME | auto-updates on change |

**Composite primary key** `(user_id, category_id, topic_id)`, exactly one
of `category_id`/`topic_id` set per row. SQLite does not enforce NOT NULL
on non-INTEGER primary-key columns, so a nullable column inside a composite
PK is valid here — a quirk worth knowing if you port this schema to
another database, where it likely won't be.

### `user_interactions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK → users.id | NOT NULL |
| article_id | INTEGER FK → articles.id | NOT NULL |
| interaction_type | TEXT | NOT NULL — one of `read`/`like`/`dislike`/`save` |
| created_at | DATETIME | NOT NULL, default now |

Composite index on `(user_id, created_at)` for fast history queries.

### `bookmarks`
| Column | Type | Notes |
|---|---|---|
| user_id | INTEGER FK → users.id | part of composite PK |
| article_id | INTEGER FK → articles.id | part of composite PK |
| created_at | DATETIME | NOT NULL, default now |

**Composite primary key** `(user_id, article_id)`. Kept separate from
`user_interactions(type='save')`: bookmarks is the canonical saved-list
table (fast `WHERE user_id=?`), while a `save` interaction is purely a
history/preference-update event — both are written on every "Save" click.

## Entity relationships (ASCII ER)

```
users 1───* user_preferences *───1 categories
users 1───* user_preferences *───1 topics       (one axis or the other, per row)
users 1───* user_interactions *───1 articles
users 1───* bookmarks *───1 articles
categories 1───* articles
articles *───* topics   (via article_topics)
articles 0..1───* articles   (is_duplicate_of, self-referential)
```

## Deviations from the original architecture draft

The plan document's Part 12 schema was a first draft; these fields were
corrected during Phase 1 verification (see the session's Phase 1 report for
the full before/after) and are the ones actually implemented:

| Original draft | As built | Why |
|---|---|---|
| `articles.source` | `articles.source_name` | canonical name, avoids clashing with Python's `source` as a keyword-ish term across services |
| `user_interactions.type` | `user_interactions.interaction_type` | same reasoning; the JSON API field is still `type` — see `docs/api.md`'s `POST /interactions` for the explicit mapping |
| `articles.category_id` NOT NULL (implied) | nullable | Phase 2 ingestion normalizes articles without a category; categorization is a later phase |
| `articles.url` UNIQUE (missing in first draft) | UNIQUE, NOT NULL | required for the ingestion pipeline's duplicate-by-url check |
| `articles.is_duplicate_of` (missing in first draft) | present, nullable FK | Phase 1 verification caught this column had never been added |
| `user_preferences` surrogate `id` PK | composite `(user_id, category_id, topic_id)` PK | matches the architecture spec's stated primary key exactly |
| `bookmarks` surrogate `id` PK | composite `(user_id, article_id)` PK | same |
| `articles.popularity_score` default 0.5 | default 0.0 | matches the spec's stated default and the ingestion normalizer's default |
