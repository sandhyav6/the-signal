"""frontend/api_client.py — thin HTTP client wrapping the FastAPI backend.

The frontend never imports backend code directly (Part 15 of the
architecture doc: "frontend/ depends only on the API (HTTP)") — this module
is its only channel to the app's data. Every call degrades gracefully: on
any network failure it shows a plain-language Streamlit error and returns
None/an empty result instead of crashing the page.
"""

import os
from typing import Optional

import requests
import streamlit as st

BACKEND_HOST = os.environ.get("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = os.environ.get("BACKEND_PORT", "8000")
BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

TIMEOUT_SECONDS = 10

# A single default user (id=1) is used throughout — this project has no
# login flow (see backend/models/models.py User docstring); seed.py always
# creates exactly this user.
DEFAULT_USER_ID = 1


def _request(method: str, path: str, **kwargs) -> Optional[dict]:
    """Make one HTTP request to the backend; never raise to the caller.

    Args:
        method: 'get', 'post', or 'put'.
        path: URL path (e.g. "/feed").
        **kwargs: forwarded to requests (params=, json=).

    Returns:
        The parsed JSON body, or None on any network/HTTP error (a
        plain-language message is shown via st.error in that case).

    Complexity: O(1) plus network latency.
    """
    try:
        resp = requests.request(method, f"{BASE_URL}{path}", timeout=TIMEOUT_SECONDS, **kwargs)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("error", resp.text)
            except ValueError:
                detail = resp.text
            st.error(f"Backend error ({resp.status_code}): {detail}")
            return None
        return resp.json()
    except requests.RequestException as e:
        st.error(f"Could not reach the backend at {BASE_URL} — is it running? ({e})")
        return None


def get_categories() -> list[dict]:
    """GET /categories -> [{id, name, slug}, ...]."""
    return _request("get", "/categories") or []


def get_feed(user_id: int, feed_type: str = "foryou", category: Optional[int] = None, page: int = 1) -> Optional[dict]:
    """GET /feed -> {user_id, type, page, articles: [{article, score, breakdown}, ...]}."""
    params = {"user_id": user_id, "type": feed_type, "page": page}
    if category is not None:
        params["category"] = category
    return _request("get", "/feed", params=params)


def get_article(article_id: int) -> Optional[dict]:
    """GET /articles/{id} -> {article, related}."""
    return _request("get", f"/articles/{article_id}")


def search(query: str, page: int = 1) -> Optional[dict]:
    """GET /search -> {query, page, total, articles}."""
    return _request("get", "/search", params={"q": query, "page": page})


def suggest(prefix: str) -> list[str]:
    """GET /search/suggest -> a list of autocomplete suggestions."""
    result = _request("get", "/search/suggest", params={"prefix": prefix})
    return result["suggestions"] if result else []


def get_trending(limit: int = 5) -> list[dict]:
    """GET /trending -> a list of {topic, score} dicts."""
    result = _request("get", "/trending", params={"limit": limit})
    return result["topics"] if result else []


def post_interaction(user_id: int, article_id: int, interaction_type: str) -> Optional[dict]:
    """POST /interactions — record a read/like/save/dislike."""
    return _request("post", "/interactions", json={"user_id": user_id, "article_id": article_id, "type": interaction_type})


def post_bookmark(user_id: int, article_id: int) -> Optional[dict]:
    """POST /bookmarks — save an article."""
    return _request("post", "/bookmarks", json={"user_id": user_id, "article_id": article_id})


def get_bookmarks(user_id: int) -> list[dict]:
    """GET /bookmarks -> a user's saved articles."""
    result = _request("get", "/bookmarks", params={"user_id": user_id})
    return result["articles"] if result else []


def get_history(user_id: int) -> list[dict]:
    """GET /history -> a user's read articles."""
    result = _request("get", "/history", params={"user_id": user_id})
    return result["articles"] if result else []


def get_preferences(user_id: int) -> dict:
    """GET /preferences -> {category_id: weight}."""
    result = _request("get", "/preferences", params={"user_id": user_id})
    return result["preferences"] if result else {}


def put_preferences(user_id: int, updates: dict) -> Optional[dict]:
    """PUT /preferences — manually set category weights."""
    return _request("put", "/preferences", json={"user_id": user_id, "updates": updates})


def post_refresh(mode: Optional[str] = None) -> Optional[dict]:
    """POST /refresh -> {added, duplicates_skipped}."""
    return _request("post", "/refresh", json={"mode": mode} if mode else {})
