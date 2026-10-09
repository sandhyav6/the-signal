"""backend/services/scheduler.py — background live-news refresh.

When the app runs in live mode (APP_ENV=live + NEWS_API_KEY), a daemon
thread calls ingestion.ingest("live") once at startup and then every
AUTO_REFRESH_MINUTES, so the feed stays current without anyone clicking
Refresh. ingest() already serializes with manual refreshes, honours the
cooldown and the daily request budget, and never raises for source
failures — this loop only needs to keep itself alive.
"""

import logging
import threading
from typing import Optional

from backend.config import settings
from backend.services import ingestion

logger = logging.getLogger(__name__)

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None


def _run(interval_seconds: float) -> None:
    """Refresh, then wait `interval_seconds` (or until stopped), forever."""
    while not _stop_event.is_set():
        try:
            result = ingestion.ingest("live")
            logger.info(
                "[scheduler._run] Auto-refresh (%s): added=%s %s",
                result["source"], result["added"], result["message"] or "",
            )
        except Exception as e:  # keep the loop alive whatever happens (DB locked, etc.)
            logger.error("[scheduler._run] Auto-refresh failed: %s", e)
        _stop_event.wait(interval_seconds)


def start() -> bool:
    """Start the background refresh thread if live mode is configured.

    Returns:
        True if a thread was started, False if auto-refresh is disabled
        (mock mode, no key, AUTO_REFRESH_MINUTES=0) or already running.

    Complexity: O(1).
    """
    global _thread
    if not settings.is_live_mode or settings.auto_refresh_minutes <= 0:
        return False
    if _thread is not None and _thread.is_alive():
        return False
    _stop_event.clear()
    _thread = threading.Thread(
        target=_run, args=(settings.auto_refresh_minutes * 60,), name="auto-refresh", daemon=True
    )
    _thread.start()
    logger.info("[scheduler.start] Auto-refresh every %s minutes", settings.auto_refresh_minutes)
    return True


def stop() -> None:
    """Signal the background thread to exit at its next wake-up. O(1)."""
    _stop_event.set()
