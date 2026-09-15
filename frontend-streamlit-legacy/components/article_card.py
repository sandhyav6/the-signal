"""frontend/components/article_card.py — reusable article card: headline,
source, relative timestamp, category badge, image/placeholder, description,
an expandable "Why am I seeing this?" score breakdown, a Related Articles
expander, and Like/Dislike/Save/Mark-read action buttons.
"""

import datetime
from typing import Optional

import streamlit as st

from frontend import api_client
from frontend.components.score_breakdown import render_score_breakdown

PLACEHOLDER_IMAGE = "https://placehold.co/800x450?text=No+Image"


def _relative_time(iso_timestamp: Optional[str]) -> str:
    """Format an ISO timestamp as a short relative string ('2h ago').

    Complexity: O(1).
    """
    if not iso_timestamp:
        return ""
    try:
        published = datetime.datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return ""
    seconds = (datetime.datetime.utcnow() - published).total_seconds()
    if seconds < 0:
        return "just now"
    if seconds < 3600:
        return f"{max(1, int(seconds // 60))}m ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h ago"
    return f"{int(seconds // 86400)}d ago"


def _render_actions(article_id: int, key_prefix: str) -> None:
    """Render the Like/Dislike/Save/Mark-read button row.

    Save both bookmarks the article (canonical saved-list) and records a
    'save' interaction (preference-engine signal) — per the architecture
    doc, these are deliberately two separate writes for one user action.
    """
    cols = st.columns(4)
    if cols[0].button("👍 Like", key=f"{key_prefix}like-{article_id}"):
        api_client.post_interaction(api_client.DEFAULT_USER_ID, article_id, "like")
        st.toast("Liked — your feed will reflect this next refresh.")
    if cols[1].button("👎 Dislike", key=f"{key_prefix}dislike-{article_id}"):
        api_client.post_interaction(api_client.DEFAULT_USER_ID, article_id, "dislike")
        st.toast("Got it — showing less like this.")
    if cols[2].button("🔖 Save", key=f"{key_prefix}save-{article_id}"):
        api_client.post_bookmark(api_client.DEFAULT_USER_ID, article_id)
        api_client.post_interaction(api_client.DEFAULT_USER_ID, article_id, "save")
        st.toast("Saved!")
    if cols[3].button("✅ Mark read", key=f"{key_prefix}read-{article_id}"):
        api_client.post_interaction(api_client.DEFAULT_USER_ID, article_id, "read")
        st.toast("Marked as read.")


def _render_related_articles(article_id: int, categories_by_id: dict, key_prefix: str) -> None:
    """Render a button-gated, lazily-fetched Related Articles list.

    A plain st.expander still executes its body on every rerun even while
    collapsed (only display is deferred, not execution) — with many cards
    on one page that meant one HTTP request per card just to build a page
    nobody had opened yet. Gating the fetch behind an explicit button +
    session_state flag means it only runs for a card the user actually
    asks to expand.
    """
    related_key = f"{key_prefix}related-shown-{article_id}"
    if st.button("🔗 Related articles", key=f"{key_prefix}related-btn-{article_id}"):
        st.session_state[related_key] = not st.session_state.get(related_key, False)

    if st.session_state.get(related_key):
        detail = api_client.get_article(article_id)
        related = detail["related"] if detail else []
        if not related:
            st.caption("No related articles found.")
        for rel in related:
            st.markdown(f"- **{rel['title']}** ({categories_by_id.get(rel.get('category_id'), '')})")


def render_article_card(
    article: dict,
    categories_by_id: dict,
    score: Optional[float] = None,
    breakdown: Optional[dict] = None,
    key_prefix: str = "",
) -> None:
    """Render one article card.

    Args:
        article: a serialized article dict (id, title, description, ...).
        categories_by_id: {category_id: category_name}, for the badge.
        score / breakdown: if given, shown in a "Why am I seeing this?"
            expander (omitted for non-ranked feeds like Latest).
        key_prefix: makes this card's widget keys unique when the same
            component is rendered many times on one page.
    """
    article_id = article["id"]
    with st.container(border=True):
        image_col, text_col = st.columns([1, 3])
        with image_col:
            st.image(article.get("image_url") or PLACEHOLDER_IMAGE, width="stretch")
        with text_col:
            category_name = categories_by_id.get(article.get("category_id"), "Uncategorized")
            source = article.get("source_name", "Unknown source")
            st.caption(f"{source} · {_relative_time(article.get('published_at'))} · 🏷️ {category_name}")
            st.subheader(article["title"])
            if article.get("description"):
                st.write(article["description"])

        with st.expander("Why am I seeing this?"):
            render_score_breakdown(score, breakdown)

        _render_related_articles(article_id, categories_by_id, key_prefix)
        _render_actions(article_id, key_prefix)
