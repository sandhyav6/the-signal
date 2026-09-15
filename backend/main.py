"""backend/main.py — FastAPI application entrypoint.

No business logic here — only app construction, router registration, and
error-handler wiring. Run with:

    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.errors import register_exception_handlers
from backend.api.routes import (
    articles,
    bookmarks,
    feed,
    history,
    interactions,
    preferences,
    refresh,
    search,
    trending,
)

app = FastAPI(title="Dynamic News Feed API", version="1.0.0")

register_exception_handlers(app)

# The React frontend's dev server proxies /api/* to this backend (see
# frontend/vite.config.js), which avoids CORS entirely for `npm run dev`.
# This middleware only matters if the built frontend is ever served from a
# different origin (e.g. `npm run preview`, or a separate static host).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles.router)
app.include_router(feed.router)
app.include_router(search.router)
app.include_router(trending.router)
app.include_router(interactions.router)
app.include_router(bookmarks.router)
app.include_router(history.router)
app.include_router(preferences.router)
app.include_router(refresh.router)


@app.get("/")
def root() -> dict:
    """Health check / landing route."""
    return {"status": "ok", "docs": "/docs"}
