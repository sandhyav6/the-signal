"""frontend/pages/trending.py — Trending: ranked topic list with counts,
click-through to a filtered view (Part 14 — implemented via /search since
the API has no dedicated per-topic feed endpoint).
"""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("🔥 Trending")
    topics = api_client.get_trending(limit=10)
    if not topics:
        st.info("Nothing trending in the last 24 hours yet.")
        return

    for t in topics:
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{t['topic']}** — score {t['score']:.1f}")
        if col2.button("View articles", key=f"trend-{t['topic']}"):
            st.session_state["trending_selected_topic"] = t["topic"]

    selected = st.session_state.get("trending_selected_topic")
    if not selected:
        return

    st.subheader(f'Articles about "{selected}"')
    categories = {c["id"]: c["name"] for c in api_client.get_categories()}
    results = api_client.search(selected)
    if not results or not results["articles"]:
        st.caption("No matching articles found.")
        return
    for article in results["articles"]:
        render_article_card(article, categories, key_prefix="trend-detail-")
