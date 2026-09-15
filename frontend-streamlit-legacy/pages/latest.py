"""frontend/pages/latest.py — Latest: plain recency feed, no personalization."""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("🕒 Latest")
    categories = {c["id"]: c["name"] for c in api_client.get_categories()}
    feed = api_client.get_feed(api_client.DEFAULT_USER_ID, feed_type="latest")
    if not feed or not feed["articles"]:
        st.info("No articles yet.")
        return
    for entry in feed["articles"]:
        render_article_card(
            entry["article"], categories,
            score=entry.get("score"), breakdown=entry.get("breakdown"),
            key_prefix="latest-",
        )
