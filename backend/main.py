"""backend/main.py — FastAPI application entrypoint.

No business logic here — only app construction, router registration, and
error-handler wiring. Run with:

    uvicorn backend.main:app --reload

API routes are always served under /api (what the React app calls). In
development they're also served at the root (what the tests and `curl`
use). With SERVE_FRONTEND=true (set in the Dockerfile) the app instead
serves the built frontend from frontend/dist at the root — page URLs like
/trending or /articles/3 overlap API paths, so in that mode the API lives
only under /api. A deployment is then one service on one URL, no CORS.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    status,
    trending,
)
from backend.api.errors import APIError
from backend.config import settings
from backend.database.seed import ensure_base_data
from backend.services import scheduler

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """On startup, make sure the database has its tables, categories and
    default user (so a fresh deployment needs no manual seed step), then
    start the live-mode auto-refresh thread. Stop it on exit."""
    ensure_base_data()
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="The Signal API", version="1.1.0", lifespan=lifespan)

register_exception_handlers(app)

# The React frontend's dev server proxies /api/* to this backend (see
# frontend/vite.config.js), which avoids CORS entirely for `npm run dev`.
# This middleware only matters if the built frontend is ever served from a
# different origin (e.g. `npm run preview`); in production the backend
# serves the build itself (see the bottom of this file).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ROUTERS = [articles, feed, search, trending, interactions, bookmarks, history, preferences, refresh, status]
for _module in _ROUTERS:
    app.include_router(_module.router, prefix="/api", include_in_schema=settings.serve_frontend)
    if not settings.serve_frontend:
        app.include_router(_module.router)


@app.get("/health")
def health() -> dict:
    """Health check for hosting platforms and uptime monitors."""
    return {"status": "ok"}


FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if settings.serve_frontend and os.path.isfile(os.path.join(FRONTEND_DIST, "index.html")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        """Serve a built frontend file, or index.html for client-side routes
        (/latest, /articles/12, ...). Unknown /api/* paths stay JSON 404s."""
        if path == "api" or path.startswith("api/"):
            raise APIError(404, f"No API route /{path}", "not_found")
        candidate = os.path.normpath(os.path.join(FRONTEND_DIST, path))
        if candidate.startswith(FRONTEND_DIST + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def root() -> dict:
        """Landing route when no frontend build is present (development)."""
        return {"status": "ok", "docs": "/docs"}
