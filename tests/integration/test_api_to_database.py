"""tests/integration/test_api_to_database.py — route-level tests proving
each database-backed (CRUD-ish) endpoint is correctly wired end-to-end, and
that every documented error case (Part 13 of the architecture doc) returns
the right status code and the standard {"error","code"} shape.
"""

import datetime

from tests.integration.conftest import (
    TECH_CATEGORY_ID,
    seed_article,
    seed_categories,
    seed_user,
)

NOW = datetime.datetime.utcnow()


def _assert_error_shape(resp, status_code, code):
    assert resp.status_code == status_code
    body = resp.json()
    assert "error" in body and "code" in body
    assert body["code"] == code


# ─── /categories ────────────────────────────────────────────────────────────

def test_list_categories(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        session.commit()
    resp = client.get("/categories")
    assert resp.status_code == 200
    names = {c["name"] for c in resp.json()}
    assert names == {"Technology", "Sports"}


# ─── /articles ──────────────────────────────────────────────────────────────

def test_list_articles_paginated(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        for i in range(1, 6):
            seed_article(session, i, f"Article {i}", published_at=NOW)
        session.commit()

    resp = client.get("/articles?page=1&limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["articles"]) == 2


def test_list_articles_bad_pagination_returns_400(client, fresh_db):
    _assert_error_shape(client.get("/articles?page=0"), 400, "bad_pagination")
    _assert_error_shape(client.get("/articles?limit=0"), 400, "bad_pagination")
    _assert_error_shape(client.get("/articles?limit=1000"), 400, "bad_pagination")


def test_get_article_detail(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "Detail Article", published_at=NOW)
        session.commit()

    resp = client.get("/articles/1")
    assert resp.status_code == 200
    assert resp.json()["article"]["id"] == 1
    assert "related" in resp.json()


def test_get_article_not_found_returns_404(client, fresh_db):
    _assert_error_shape(client.get("/articles/999"), 404, "article_not_found")


# ─── /interactions ──────────────────────────────────────────────────────────

def test_post_interaction_updates_preference_and_returns_201(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        seed_article(session, 1, "A", category_id=TECH_CATEGORY_ID, published_at=NOW)
        session.commit()

    resp = client.post("/interactions", json={"user_id": 1, "article_id": 1, "type": "like"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["preference_weight"] == 0.20  # 0.1 baseline + 0.10 like

    prefs = client.get("/preferences?user_id=1").json()["preferences"]
    assert prefs[str(TECH_CATEGORY_ID)] == 0.20


def test_post_interaction_invalid_type_returns_400(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        seed_article(session, 1, "A", published_at=NOW)
        session.commit()

    _assert_error_shape(
        client.post("/interactions", json={"user_id": 1, "article_id": 1, "type": "share"}),
        400, "invalid_interaction_type",
    )


def test_post_interaction_unknown_user_returns_404(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_article(session, 1, "A", published_at=NOW)
        session.commit()

    _assert_error_shape(
        client.post("/interactions", json={"user_id": 999, "article_id": 1, "type": "like"}),
        404, "user_not_found",
    )


def test_post_interaction_unknown_article_returns_404(client, fresh_db):
    with fresh_db() as session:
        seed_user(session)
        session.commit()

    _assert_error_shape(
        client.post("/interactions", json={"user_id": 1, "article_id": 999, "type": "like"}),
        404, "article_not_found",
    )


# ─── /bookmarks ─────────────────────────────────────────────────────────────

def test_post_and_get_bookmarks(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        seed_article(session, 1, "A", published_at=NOW)
        session.commit()

    create_resp = client.post("/bookmarks", json={"user_id": 1, "article_id": 1})
    assert create_resp.status_code == 201
    assert create_resp.json()["created"] is True

    dup_resp = client.post("/bookmarks", json={"user_id": 1, "article_id": 1})
    assert dup_resp.status_code == 201
    assert dup_resp.json()["created"] is False

    list_resp = client.get("/bookmarks?user_id=1")
    assert list_resp.status_code == 200
    assert [a["id"] for a in list_resp.json()["articles"]] == [1]


def test_post_bookmark_unknown_user_returns_404(client, fresh_db):
    with fresh_db() as session:
        seed_article(session, 1, "A", published_at=NOW)
        session.commit()
    _assert_error_shape(
        client.post("/bookmarks", json={"user_id": 999, "article_id": 1}), 404, "user_not_found"
    )


def test_get_bookmarks_unknown_user_returns_404(client, fresh_db):
    _assert_error_shape(client.get("/bookmarks?user_id=999"), 404, "user_not_found")


# ─── /history ───────────────────────────────────────────────────────────────

def test_get_history_returns_read_articles(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        seed_article(session, 1, "A", published_at=NOW)
        session.commit()

    client.post("/interactions", json={"user_id": 1, "article_id": 1, "type": "read"})
    resp = client.get("/history?user_id=1")
    assert resp.status_code == 200
    assert [a["id"] for a in resp.json()["articles"]] == [1]


def test_get_history_unknown_user_returns_404(client, fresh_db):
    _assert_error_shape(client.get("/history?user_id=999"), 404, "user_not_found")


# ─── /preferences ───────────────────────────────────────────────────────────

def test_get_preferences(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        session.commit()
    resp = client.get("/preferences?user_id=1")
    assert resp.status_code == 200
    assert resp.json()["preferences"] == {str(TECH_CATEGORY_ID): 0.1, "2": 0.1}


def test_get_preferences_unknown_user_returns_404(client, fresh_db):
    _assert_error_shape(client.get("/preferences?user_id=999"), 404, "user_not_found")


def test_put_preferences_updates_weight(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        session.commit()

    resp = client.put("/preferences", json={"user_id": 1, "updates": {str(TECH_CATEGORY_ID): 0.75}})
    assert resp.status_code == 200
    assert resp.json()["preferences"][str(TECH_CATEGORY_ID)] == 0.75


def test_put_preferences_out_of_range_weight_returns_400(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        session.commit()
    _assert_error_shape(
        client.put("/preferences", json={"user_id": 1, "updates": {str(TECH_CATEGORY_ID): 5.0}}),
        400, "invalid_weight",
    )


def test_put_preferences_unknown_category_returns_400(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        seed_user(session)
        session.commit()
    _assert_error_shape(
        client.put("/preferences", json={"user_id": 1, "updates": {"9999": 0.5}}),
        400, "invalid_category",
    )


def test_put_preferences_unknown_user_returns_404(client, fresh_db):
    with fresh_db() as session:
        seed_categories(session)
        session.commit()
    _assert_error_shape(
        client.put("/preferences", json={"user_id": 999, "updates": {str(TECH_CATEGORY_ID): 0.5}}),
        404, "user_not_found",
    )


# ─── /refresh ───────────────────────────────────────────────────────────────

def test_post_refresh_mock_returns_counts(client, fresh_db):
    resp = client.post("/refresh", json={"mode": "mock"})
    assert resp.status_code == 200
    body = resp.json()
    assert "added" in body and "duplicates_skipped" in body
    assert body["added"] > 0


def test_post_refresh_no_body_defaults_to_configured_mode(client, fresh_db):
    resp = client.post("/refresh")
    assert resp.status_code == 200
