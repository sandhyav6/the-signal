"""tests/unit/test_classification.py — keyword category classification and
topic extraction (algorithms/classification.py)."""

from backend.algorithms.classification import classify_category, extract_topics


def test_classify_category_picks_best_keyword_match():
    assert classify_category("Senate votes on election bill as Congress returns") == "politics"
    assert classify_category("Stocks rally as inflation cools and the Fed holds") == "business"
    assert classify_category("NASA telescope spots a new planet") == "science"


def test_classify_category_returns_none_without_any_match():
    assert classify_category("Local bakery wins hearts") is None
    assert classify_category("") is None


def test_classify_category_tie_resolves_to_first_listed_category():
    keywords = {"a": frozenset({"x"}), "b": frozenset({"x"})}
    assert classify_category("x", keywords) == "a"


def test_extract_topics_prefers_named_entity_phrases():
    topics = extract_topics(
        "Federal Reserve holds rates steady",
        "The Federal Reserve kept rates unchanged, Jerome Powell said.",
    )
    assert topics[0] == "federal reserve"
    assert "jerome powell" in topics
    # "federal"/"reserve" are already covered by the phrase.
    assert "federal" not in topics and "reserve" not in topics


def test_extract_topics_ignores_stopwords_and_respects_limit():
    topics = extract_topics("What will the markets do now", "", max_topics=2)
    assert len(topics) <= 2
    assert not {"what", "will", "the", "now"} & set(topics)


def test_extract_topics_skips_phrase_detection_for_title_case_headlines():
    topics = extract_topics("Lakers Beat Celtics In Overtime Thriller", "")
    assert all(len(t.split()) == 1 for t in topics)


def test_extract_topics_empty_input():
    assert extract_topics("", "") == []
