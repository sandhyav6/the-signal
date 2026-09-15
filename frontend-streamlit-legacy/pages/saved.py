"""frontend/pages/saved.py — Saved: bookmarked articles."""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("🔖 Saved")
    categories = {c["id"]: c["name"] for c in api_client.get_categories()}
    articles = api_client.get_bookmarks(api_client.DEFAULT_USER_ID)
    if not articles:
        st.info("You haven't saved any articles yet.")
        return
    for article in articles:
        render_article_card(article, categories, key_prefix="saved-")
