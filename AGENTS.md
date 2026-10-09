# AGENTS.md — Development Rules & Protocol

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
| 11    | Live NewsAPI data & robustness       | ✅ Done     |
