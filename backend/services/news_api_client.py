"""backend/services/news_api_client.py — the only module that talks to
NewsAPI.org. Fetches top headlines per category and maps them into the raw
article shape the normalizer expects.

Design notes:
  - The API key travels in the `X-Api-Key` header, never the query string,
    so it can't leak into log lines or exception messages (requests puts
    the full URL, query string included, into its error text).
  - NewsAPI has no "politics" category, so politics stories are taken from
    the "general" feed and classified by keyword in ingestion.
  - A per-UTC-day request counter enforces a budget below the free plan's
    100 requests/day, so an aggressive refresh habit degrades to cached
    data instead of getting the key rate-limited.
"""

import datetime
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

import requests

from backend.config import settings

logger = logging.getLogger(__name__)

# Our category slug -> NewsAPI category. None = "classify it ourselves".
NEWS_API_CATEGORIES: dict[str, Optional[str]] = {
    "technology": "technology",
    "science": "science",
    "business": "business",
    "sports": "sports",
    "health": "health",
    "entertainment": "entertainment",
}
GENERAL_FEED = "general"
REQUEST_TIMEOUT_SECONDS = 10

# NewsAPI error codes after which further requests this refresh are pointless.
_FATAL_ERROR_CODES = {"apiKeyInvalid", "apiKeyDisabled", "apiKeyExhausted", "apiKeyMissing", "rateLimited"}


class NewsApiError(Exception):
    """A NewsAPI request failed. `code` is NewsAPI's error code when known."""

    def __init__(self, message: str, code: str = "requestFailed") -> None:
        super().__init__(message)
        self.code = code

    @property
    def is_fatal(self) -> bool:
        """True if retrying other categories in this refresh is pointless."""
        return self.code in _FATAL_ERROR_CODES


@dataclass
class _Quota:
    """Requests made so far on one UTC day."""
    day: datetime.date = field(default_factory=lambda: datetime.datetime.utcnow().date())
    used: int = 0


_quota = _Quota()
_quota_lock = threading.Lock()


def requests_used_today() -> int:
    """Return how many NewsAPI requests were made today (UTC). O(1)."""
    with _quota_lock:
        _roll_quota_day()
        return _quota.used


def reset_quota() -> None:
    """Reset the daily request counter (used by tests). O(1)."""
    global _quota
    with _quota_lock:
        _quota = _Quota()


def _roll_quota_day() -> None:
    """Start a fresh counter when the UTC day changes. Caller holds the lock."""
    global _quota
    today = datetime.datetime.utcnow().date()
    if _quota.day != today:
        _quota = _Quota(day=today)


def _reserve_requests(count: int) -> bool:
    """Atomically reserve `count` requests from today's budget.

    Returns:
        False (reserving nothing) if the budget can't cover all of them.

    Complexity: O(1).
    """
    with _quota_lock:
        _roll_quota_day()
        if _quota.used + count > settings.news_api_daily_budget:
            return False
        _quota.used += count
        return True


def _release_requests(count: int) -> None:
    """Return `count` reserved-but-unused requests to today's budget. O(1)."""
    with _quota_lock:
        _quota.used = max(0, _quota.used - count)


def _endpoint() -> str:
    """Return the top-headlines URL, tolerating a NEWS_API_URL that already
    includes the endpoint path. O(1)."""
    base = settings.news_api_url.rstrip("/")
    return base if base.endswith("/top-headlines") else f"{base}/top-headlines"


def _error_from_response(response: requests.Response) -> NewsApiError:
    """Build a NewsApiError from a non-2xx NewsAPI response body. O(1)."""
    try:
        body = response.json()
        return NewsApiError(body.get("message", response.reason), body.get("code", "requestFailed"))
    except (ValueError, AttributeError):
        return NewsApiError(f"HTTP {response.status_code}", "requestFailed")


def fetch_category(news_api_category: str) -> list[dict]:
    """Fetch one category of top headlines from NewsAPI.

    Args:
        news_api_category: a NewsAPI category name (e.g. "technology").

    Returns:
        The raw NewsAPI article objects (list of dicts).

    Raises:
        NewsApiError: on network failure, a non-2xx status, or a payload
            that isn't {"status": "ok", "articles": [...]}.

    Complexity: one HTTP round trip + O(n) JSON parse.
    """
    try:
        response = requests.get(
            _endpoint(),
            params={
                "country": settings.news_api_country,
                "category": news_api_category,
                "pageSize": settings.news_api_page_size,
            },
            headers={"X-Api-Key": settings.news_api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as e:
        raise NewsApiError(f"network error: {type(e).__name__}", "networkError") from e
    if not response.ok:
        raise _error_from_response(response)
    try:
        payload = response.json()
    except ValueError as e:
        raise NewsApiError("response was not JSON", "malformedResponse") from e
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise NewsApiError("unexpected response shape", "malformedResponse")
    return payload["articles"]


def to_raw_article(item: dict, category_slug: Optional[str], rank: int, total: int) -> dict:
    """Map one NewsAPI article object into our raw article shape.

    popularity_score is seeded from the headline's position in NewsAPI's
    ranked list (top story ~0.7, last ~0.3) — the only importance signal
    the API exposes — so live articles aren't all tied at zero popularity.

    Raises:
        AttributeError if `item` isn't a dict (caller treats as malformed).

    Complexity: O(1).
    """
    position = 1.0 - rank / max(1, total)
    return {
        "title": item.get("title"),
        "description": item.get("description"),
        "url": item.get("url"),
        "image_url": item.get("urlToImage"),
        "source_name": (item.get("source") or {}).get("name"),
        "author": item.get("author"),
        "published_at": item.get("publishedAt"),
        "popularity_score": round(0.3 + 0.4 * position, 3),
        "category_slug": category_slug,
    }


@dataclass
class FetchResult:
    """Outcome of one full live fetch across every category."""
    articles: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    fatal_error: Optional[NewsApiError] = None


def _feeds_to_fetch() -> list[tuple[Optional[str], str]]:
    """(our category slug or None, NewsAPI category) pairs for one refresh."""
    return [(slug, api_cat) for slug, api_cat in NEWS_API_CATEGORIES.items()] + [(None, GENERAL_FEED)]


def fetch_all() -> FetchResult:
    """Fetch every category's top headlines, tolerating partial failure.

    One failed category is recorded and skipped; a fatal error (invalid
    key, rate limit) stops the remaining requests. Articles from the
    "general" feed get category_slug=None for keyword classification.

    Returns:
        A FetchResult with whatever articles were fetched plus error notes.
        If today's request budget can't cover a full refresh, nothing is
        requested and fatal_error is set to a "budgetExhausted" error.

    Complexity: c HTTP requests (c = categories) + O(n) mapping.
    """
    feeds = _feeds_to_fetch()
    result = FetchResult()
    if not _reserve_requests(len(feeds)):
        result.fatal_error = NewsApiError("daily NewsAPI request budget reached", "budgetExhausted")
        return result
    for done, (slug, api_category) in enumerate(feeds, start=1):
        try:
            items = fetch_category(api_category)
            result.articles.extend(to_raw_article(item, slug, i, len(items)) for i, item in enumerate(items))
        except NewsApiError as e:
            logger.error("[news_api_client.fetch_all] %s feed failed: %s (%s)", api_category, e, e.code)
            result.errors.append(f"{api_category}: {e.code}")
            if e.is_fatal:
                result.fatal_error = e
                _release_requests(len(feeds) - done)
                break
        except AttributeError as e:
            logger.error("[news_api_client.fetch_all] %s feed malformed item: %s", api_category, e)
            result.errors.append(f"{api_category}: malformedResponse")
    return result
