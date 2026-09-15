"""frontend/pages/categories.py — Categories: horizontal chips filter the feed."""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("🗂️ Categories")
    categories = api_client.get_categories()
    if not categories:
        st.info("No categories found.")
        return
    categories_by_id = {c["id"]: c["name"] for c in categories}

    cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        if cols[i].button(cat["name"], key=f"cat-{cat['id']}"):
            st.session_state["selected_category_id"] = cat["id"]

    selected_id = st.session_state.get("selected_category_id")
    if selected_id is None:
        st.info("Pick a category above to see its feed.")
        return

    st.subheader(f"{categories_by_id.get(selected_id, '')} feed")
    feed = api_client.get_feed(api_client.DEFAULT_USER_ID, feed_type="category", category=selected_id)
    if not feed or not feed["articles"]:
        st.caption("No articles in this category yet.")
        return
    for entry in feed["articles"]:
        render_article_card(
            entry["article"], categories_by_id,
            score=entry.get("score"), breakdown=entry.get("breakdown"),
            key_prefix="cat-feed-",
        )
