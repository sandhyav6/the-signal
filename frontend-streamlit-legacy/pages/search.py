"""frontend/pages/search.py — Search: text input with a live suggestion
list backed by /search/suggest, plus results below (Part 14).
"""

import streamlit as st

from frontend import api_client
from frontend.components.article_card import render_article_card


def render() -> None:
    st.header("🔍 Search")
    query = st.text_input("Search articles", key="search_query")

    if not query:
        st.info("Type to search article titles and descriptions.")
        return

    suggestions = api_client.suggest(query)
    if suggestions:
        st.caption("Suggestions: " + ", ".join(suggestions[:8]))

    categories = {c["id"]: c["name"] for c in api_client.get_categories()}
    results = api_client.search(query)
    if not results or not results["articles"]:
        st.caption(f'No results for "{query}".')
        return

    st.caption(f"{results['total']} result(s)")
    for article in results["articles"]:
        render_article_card(article, categories, key_prefix="search-")
