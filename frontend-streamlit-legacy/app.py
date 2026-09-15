"""frontend/app.py — Streamlit entrypoint: sidebar controls (mode toggle,
Refresh Feed button, dynamic-feed indicators) plus page navigation.

Uses st.navigation/st.Page (not the classic pages/-folder auto-discovery,
which would otherwise fire on its own and fight with these sidebar
controls) so each frontend/pages/*.py module's render() function becomes
one navigable page.

Run with:
    streamlit run frontend/app.py
"""

import datetime
import os
import sys

# `streamlit run frontend/app.py` invokes the `streamlit` console script
# directly, which does not add the project root to sys.path (only `python -m
# streamlit run ...` does that) — without this, the `from frontend import
# ...` imports below fail with "ModuleNotFoundError: No module named
# 'frontend'" the moment a browser actually loads the page. Same pattern
# already used by backend/database/seed.py and every test file.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from frontend import api_client
from frontend.pages import categories as categories_page
from frontend.pages import history as history_page
from frontend.pages import home as home_page
from frontend.pages import latest as latest_page
from frontend.pages import preferences as preferences_page
from frontend.pages import saved as saved_page
from frontend.pages import search as search_page
from frontend.pages import trending as trending_page

st.set_page_config(page_title="Dynamic News Feed", page_icon="📰", layout="wide")


def _render_sidebar_controls() -> None:
    """Mode toggle, Refresh Feed button, and the dynamic-feed indicators
    ("N new articles" banner, "last updated Xs ago") — Part 14.
    """
    st.sidebar.title("📰 Dynamic News Feed")
    mode = st.sidebar.radio("Mode", ["mock", "live"], key="app_mode", horizontal=True)

    if st.sidebar.button("🔄 Refresh Feed"):
        result = api_client.post_refresh(mode)
        if result is not None:
            st.session_state["last_refresh_at"] = datetime.datetime.utcnow()
            st.sidebar.success(
                f"🔄 {result['added']} new articles added "
                f"({result['duplicates_skipped']} already seen)"
            )

    last_refresh_at = st.session_state.get("last_refresh_at")
    if last_refresh_at:
        seconds_ago = int((datetime.datetime.utcnow() - last_refresh_at).total_seconds())
        st.sidebar.caption(f"Last updated {seconds_ago}s ago")

    st.sidebar.divider()


def main() -> None:
    """App entrypoint: render sidebar controls, then dispatch to the
    selected page via st.navigation.
    """
    _render_sidebar_controls()

    # Every page module names its entry function `render` — st.Page infers
    # the URL pathname from the callable's __name__ by default, so without
    # an explicit url_path every page would collide on "render".
    pages = [
        st.Page(home_page.render, title="Home / For You", icon="🏠", url_path="home", default=True),
        st.Page(latest_page.render, title="Latest", icon="🕒", url_path="latest"),
        st.Page(trending_page.render, title="Trending", icon="🔥", url_path="trending"),
        st.Page(categories_page.render, title="Categories", icon="🗂️", url_path="categories"),
        st.Page(search_page.render, title="Search", icon="🔍", url_path="search"),
        st.Page(saved_page.render, title="Saved", icon="🔖", url_path="saved"),
        st.Page(history_page.render, title="History", icon="📜", url_path="history"),
        st.Page(preferences_page.render, title="Preferences", icon="⚙️", url_path="preferences"),
    ]
    st.navigation(pages).run()


if __name__ == "__main__":
    main()
