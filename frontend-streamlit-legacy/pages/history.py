"""frontend/pages/history.py — History: articles marked read."""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("📜 History")
    categories = {c["id"]: c["name"] for c in api_client.get_categories()}
    articles = api_client.get_history(api_client.DEFAULT_USER_ID)
    if not articles:
        st.info("No reading history yet.")
        return
    for article in articles:
        render_article_card(article, categories, key_prefix="history-")
