"""tests/unit/test_normalizer.py — unit tests for services.normalizer.normalize.

Covers: well-formed input, missing description/image/author, malformed date,
HTML in description, and missing title (rejection).
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.normalizer import normalize


def _base_raw(**overrides) -> dict:
    raw = {
        "title": "Sample Article Title",
        "description": "A short description.",
        "url": "https://example.com/articles/1",
        "image_url": "https://example.com/img.jpg",
        "source_name": "Example News",
        "author": "Jane Doe",
        "published_at": "2026-09-10T12:00:00",
        "popularity_score": 0.5,
    }
    raw.update(overrides)
    return raw


def test_well_formed_input_produces_correct_dict():
    """A fully-populated raw article normalizes to the expected shape."""
    result = normalize(_base_raw())
    assert result is not None
    assert result["title"] == "Sample Article Title"
    assert result["description"] == "A short description."
    assert result["url"] == "https://example.com/articles/1"
    assert result["image_url"] == "https://example.com/img.jpg"
    assert result["source_name"] == "Example News"
    assert result["author"] == "Jane Doe"
    assert result["category_id"] is None
    assert result["is_duplicate_of"] is None
    assert result["popularity_score"] == 0.5
    assert result["published_at"] == datetime.datetime(2026, 9, 10, 12, 0, 0)
    assert isinstance(result["content_hash"], str) and len(result["content_hash"]) == 64
    assert isinstance(result["fetched_at"], datetime.datetime)


def test_missing_description_defaults_to_empty_string():
    """Missing description must not crash, and defaults to ''."""
    raw = _base_raw()
    del raw["description"]
    result = normalize(raw)
    assert result is not None
    assert result["description"] == ""


def test_missing_image_and_author_default_to_none():
    """Missing image_url/author must not crash, and default to None."""
    raw = _base_raw()
    del raw["image_url"]
    del raw["author"]
    result = normalize(raw)
    assert result is not None
    assert result["image_url"] is None
    assert result["author"] is None


def test_malformed_date_defaults_gracefully():
    """An unparseable published_at must not crash; defaults to ingestion time."""
    raw = _base_raw(published_at="not-a-real-date")
    before = datetime.datetime.utcnow()
    result = normalize(raw)
    after = datetime.datetime.utcnow()
    assert result is not None
    assert before <= result["published_at"] <= after


def test_html_in_description_is_stripped():
    """HTML tags in title/description must be removed."""
    raw = _base_raw(
        title="<b>Bold</b> Headline",
        description="<p>Paragraph</p> with <a href='#'>a link</a>.",
    )
    result = normalize(raw)
    assert result is not None
    assert "<" not in result["title"] and ">" not in result["title"]
    assert "<" not in result["description"] and ">" not in result["description"]
    assert result["title"] == "Bold Headline"


def test_missing_title_is_rejected():
    """An article with no title cannot be normalized; normalize() returns None."""
    raw = _base_raw()
    del raw["title"]
    assert normalize(raw) is None

    raw_blank = _base_raw(title="   ")
    assert normalize(raw_blank) is None
