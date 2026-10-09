"""backend/services/maintenance.py — one-off reprocessing of articles that
are already stored, for databases created before ingestion learned to
categorize, tag topics, and merge near-duplicates:

    python -m backend.services.maintenance

Safe to run repeatedly: it only fills in what's missing (a NULL category,
an article with no topics) and only links articles not already linked.
"""

import logging

from backend.algorithms.classification import classify_category, extract_topics
from backend.algorithms.deduplication import link_near_duplicates
from backend.database import repository
from backend.services.ingestion import NEAR_DUPLICATE_THRESHOLD, NEAR_DUPLICATE_WINDOW_HOURS

logger = logging.getLogger(__name__)


def reprocess() -> dict:
    """Backfill categories and topics, then link near-duplicate stories.

    Returns:
        {"categorized": int, "tagged": int, "linked_duplicates": int}

    Complexity: O(n * w) — dominated by the windowed near-duplicate pass
    (see algorithms.deduplication.link_near_duplicates).
    """
    slug_map = repository.get_category_slug_map()
    articles = repository.get_articles_with_topics()
    counts = {"categorized": 0, "tagged": 0, "linked_duplicates": 0}

    for article in articles:
        text = f"{article['title']} {article['description'] or ''}"
        if article["category"] is None:
            slug = classify_category(text)
            if slug in slug_map:
                repository.set_article_category(article["id"], slug_map[slug])
                counts["categorized"] += 1
        if not article["topics"]:
            repository.link_article_topics(article["id"], extract_topics(article["title"], article["description"] or ""))
            counts["tagged"] += 1

    canonical = [a for a in articles if a["is_duplicate_of"] is None]
    links = link_near_duplicates(canonical, NEAR_DUPLICATE_THRESHOLD, NEAR_DUPLICATE_WINDOW_HOURS)
    repository.set_duplicate_links(links)
    counts["linked_duplicates"] = len(links)
    return counts


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = reprocess()
    print(
        f"Reprocessed: categorized={result['categorized']} tagged={result['tagged']} "
        f"linked_duplicates={result['linked_duplicates']}"
    )
