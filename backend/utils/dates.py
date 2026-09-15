"""backend/utils/dates.py — date parsing helpers for ingested articles."""

import datetime
import logging

from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


def parse_published_at(
    raw_date: str | None, fallback: datetime.datetime | None = None
) -> datetime.datetime:
    """Parse a published_at timestamp from an arbitrary source format.

    Never raises: an unparseable or missing date defaults to `fallback`
    (current ingestion time) with a warning logged, rather than dropping
    the article or crashing the pipeline.

    Args:
        raw_date: raw date string from an API/RSS/mock source, or None.
        fallback: datetime to use if parsing fails or raw_date is falsy;
            defaults to the current UTC time.

    Returns:
        A parsed (or fallback) timezone-naive UTC datetime.

    Complexity: O(1).
    """
    fallback = fallback or datetime.datetime.utcnow()
    if not raw_date:
        logger.warning(
            "[dates.parse_published_at] Missing published_at, defaulting to %s",
            fallback,
        )
        return fallback
    try:
        parsed = dateutil_parser.parse(raw_date)
    except (ValueError, OverflowError, TypeError) as e:
        logger.warning(
            "[dates.parse_published_at] Unparseable date %r (%s), defaulting to %s",
            raw_date, e, fallback,
        )
        return fallback
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return parsed
