"""frontend/pages/home.py — Home / For You: personalized feed + a small
Trending Now widget in a sidebar column (Part 14).
"""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("🏠 For You")

    main_col, side_col = st.columns([3, 1])

    with main_col:
        categories = {c["id"]: c["name"] for c in api_client.get_categories()}
        feed = api_client.get_feed(api_client.DEFAULT_USER_ID, feed_type="foryou")
        if not feed or not feed["articles"]:
            st.info("No articles yet — try Refresh Feed in the sidebar.")
        else:
            for entry in feed["articles"]:
                render_article_card(
                    entry["article"], categories,
                    score=entry.get("score"), breakdown=entry.get("breakdown"),
                    key_prefix="home-",
                )

    with side_col:
        st.subheader("🔥 Trending Now")
        topics = api_client.get_trending(limit=5)
        if not topics:
            st.caption("Nothing trending in the last 24h yet.")
        for t in topics:
            st.write(f"**{t['topic']}** — {t['score']:.1f}")
