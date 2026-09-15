# Development Rules & Protocol

> This is a human-readable mirror of [`AGENTS.md`](../AGENTS.md) at the
> project root, which is the file coding agents actually load at the start
> of a session. Keep the two in sync if either changes.

## Project: Dynamic News Feed (DAA Project)

This file governs how every agent (human or AI) must behave when working on this project.
Read this file at the start of every session before touching any code.

---

## Cardinal Rules

1. **Work in phases.** Never implement Phase N+1 until Phase N's tests pass and are documented.
2. **Inspect before modifying.** Always read the current file before editing it.
3. **Error protocol:** Identify exact error + file + function → reproduce with minimal test → fix
   root cause with smallest change → re-run specific test → re-run full suite → continue.
4. **Never expose secrets.** `.env` is git-ignored. App must run with no `.env` present.
5. **Graceful degradation.** Live API failure → cached data → mock data → "using sample data"
   indicator. Never raise 500 to the client for API failures.
6. **Algorithms are pure.** No file in `backend/algorithms/` imports from `api/`, `services/`,
   or `database/`. Plain dicts/lists/dataclasses in and out only.
7. **Separation of concerns:**
   - `api/routes/` → parse requests, call services, return responses
   - `services/` → orchestrate business logic
   - `algorithms/` → pure logic, independently testable
   - `database/` + `models/` → persistence only
8. **No new dependencies** unless the current phase is impossible without them.
9. **Never break previous phases.** Run full test suite before declaring any phase done.
10. **No ambiguity shortcuts.** Re-read the spec, make the smallest reasonable assumption,
    never invent new architecture.

---

## Coding Conventions

- **Type hints** on all function signatures.
- **Docstrings** on every public function: purpose, complexity, parameters.
- **Function length**: ≤ ~40 lines. Split anything larger.
- **No bare `except: pass`**. Catch specific exceptions and log clearly.
- **No raw SQL** in route files. No algorithm logic in routes.
- **No deletion of functionality** to silence an error.

---

## Phase Completion Checklist

Before declaring a phase complete:
- [ ] All new code has type hints and docstrings
- [ ] All tests for this phase pass (`pytest tests/ -v`)
- [ ] No existing tests broken
- [ ] No secrets in code
- [ ] Functions are ≤ 40 lines
- [ ] Phase summary written (what was built, what tests pass)

---

## Error Handling Template

```python
import logging
logger = logging.getLogger(__name__)

try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"[module.function] Failed: {e}")
    # fallback behavior here
```

---

## Phase Status

| Phase | Description                          | Status      |
|-------|--------------------------------------|-------------|
| 1     | Setup, DB, Models, Mock Data         | ✅ Done     |
| 2     | Ingestion, Normalization, Storage    | ✅ Done     |
| 3     | Core Algorithms                      | ✅ Done     |
| 4     | Feed Generation Engine               | ✅ Done     |
| 5     | Personalization                      | ✅ Done     |
| 6     | API                                  | ✅ Done     |
| 7     | Frontend                             | ✅ Done     |
| 8     | Testing Completeness                 | ✅ Done     |
| 9     | Benchmarking                         | ✅ Done     |
| 10    | Documentation & Polish               | ✅ Done     |

---

## Real deviations discovered while building (kept here for context)

These are places where the rules above caught a genuine bug or forced a
documented, deliberate exception — useful context for anyone continuing
this project:

- **SQLAlchemy 2.0 Annotated Declarative** required `__allow_unmapped__ = True`
  on `Base` — the codebase's `field: type = Column(...)` style predates
  SQLAlchemy 2.0's `Mapped[...]` convention.
- **`insert_article()` returns `(id, was_created)`**, not just `id` — a
  caller that only pre-checks by content_hash can still hit a `url`
  collision inside `insert_article`, and needs the explicit flag to count
  added-vs-duplicate correctly (found by running `POST /refresh` against
  an already-seeded database, not by inspection).
- **`fetch_live_articles()` catches `(KeyError, TypeError, AttributeError)`**
  in addition to `requests.RequestException` — a malformed NewsAPI response
  shape (e.g. a JSON array instead of an object) previously crashed with an
  uncaught `AttributeError`.
- **`set_user_category_weight()` deletes-then-reinserts** rather than
  mutating an existing row — SQLAlchemy's ORM refuses to emit an `UPDATE`
  for a row whose primary key includes a NULL column, even though SQLite
  itself allows it (`user_preferences`'s composite PK has a nullable
  `topic_id`).
- **Two SQLite `:memory:` gotchas** hit during testing: (1) a fresh
  connection to `:memory:` from a different thread is a distinct, empty
  database — `FastAPI TestClient` runs sync routes in a background thread,
  so API-level tests need `poolclass=StaticPool`; (2) none needed for the
  service-level tests, since those never cross a thread boundary.
