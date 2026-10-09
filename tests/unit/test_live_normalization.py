"""tests/unit/test_live_normalization.py — the normalization rules real
NewsAPI data needs: publisher-suffix stripping, entity decoding, rejecting
unusable items, and near-duplicate matching."""

from backend.algorithms.deduplication import find_near_duplicate
from backend.services.normalizer import UNKNOWN_SOURCE, normalize
from backend.utils.text_cleaning import strip_html_tags, strip_source_suffix


def _raw(**overrides):
    raw = {"title": "Fed holds rates - Reuters", "url": "https://r.com/1", "source_name": "Reuters"}
    raw.update(overrides)
    return raw


def test_strip_source_suffix_only_when_it_matches_the_source():
    assert strip_source_suffix("Fed holds rates - Reuters", "Reuters") == "Fed holds rates"
    assert strip_source_suffix("Fed holds rates | CNN Business", "CNN") == "Fed holds rates"
    assert strip_source_suffix("Spider-Man - a review", "Variety") == "Spider-Man - a review"
    assert strip_source_suffix("Fed holds rates - Reuters", None) == "Fed holds rates - Reuters"


def test_strip_html_tags_decodes_entities():
    assert strip_html_tags("AT&amp;T <b>earnings</b>") == "AT&T earnings"


def test_normalize_strips_publisher_suffix_so_hashes_match_across_outlets():
    a = normalize(_raw())
    b = normalize(_raw(title="Fed holds rates - AP News", source_name="AP News", url="https://ap.org/1"))
    assert a["title"] == "Fed holds rates"
    assert a["content_hash"] == b["content_hash"]


def test_normalize_rejects_removed_and_url_less_articles():
    assert normalize(_raw(title="[Removed]")) is None
    assert normalize(_raw(url=None)) is None
    assert normalize(_raw(url="  ")) is None


def test_normalize_defaults_missing_source_name():
    assert normalize(_raw(source_name=None))["source_name"] == UNKNOWN_SOURCE


def test_normalize_passes_through_source_hints():
    result = normalize(_raw(category_slug="business", topics=["Fed", 3]))
    assert result["category_slug"] == "business"
    assert result["topics"] == ["fed"]


def test_find_near_duplicate_returns_best_match_above_threshold():
    candidates = [
        {"id": 1, "title": "Apple unveils new iPhone with faster chip", "description": ""},
        {"id": 2, "title": "Lakers beat Celtics", "description": ""},
    ]
    assert find_near_duplicate("Apple unveils new iPhone with a faster chip", candidates, 0.6) == 1
    assert find_near_duplicate("Senate passes budget bill tonight", candidates, 0.6) is None


def test_find_near_duplicate_ignores_low_signal_text():
    candidates = [{"id": 1, "title": "Big win", "description": ""}]
    assert find_near_duplicate("Big win", candidates, 0.1) is None


def test_link_near_duplicates_links_later_copy_within_window_only():
    import datetime
    from backend.algorithms.deduplication import link_near_duplicates

    t0 = datetime.datetime(2026, 10, 1, 12)
    articles = [
        {"id": 2, "title": "Apple unveils new iPhone with faster chip", "description": "",
         "published_at": t0 + datetime.timedelta(hours=2)},
        {"id": 1, "title": "Apple unveils new iPhone with a faster chip", "description": "",
         "published_at": t0},
        {"id": 3, "title": "Apple unveils new iPhone with faster chip", "description": "",
         "published_at": t0 + datetime.timedelta(days=5)},  # outside the 48h window
        {"id": 4, "title": "Lakers beat Celtics in overtime", "description": "", "published_at": t0},
    ]
    assert link_near_duplicates(articles, threshold=0.6, window_hours=48) == {2: 1}
