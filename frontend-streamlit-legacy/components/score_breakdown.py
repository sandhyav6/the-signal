"""frontend/components/score_breakdown.py — renders a ranking score
breakdown, matching the "why you're seeing this" example format from the
architecture doc (Part 6): one line per weighted term, plus the final score.
"""

from typing import Optional

import streamlit as st

_LABELS = {
    "interest": "Matches your interests",
    "recency": "Recently published",
    "popularity": "Popular",
    "keyword_relevance": "Matches your search",
    "repetition_penalty": "Diversity adjustment",
}


def render_score_breakdown(score: Optional[float], breakdown: Optional[dict]) -> None:
    """Render one article's ranking explanation.

    Args:
        score: the final ranking score (None for a non-ranked entry, e.g.
            the plain-recency Latest feed).
        breakdown: the dict returned by algorithms.ranking.compute_score,
            or None.
    """
    if score is None or not breakdown:
        st.caption("This article isn't personally ranked (Latest feed).")
        return

    for key, label in _LABELS.items():
        term = breakdown.get(key)
        if not term or term["contribution"] == 0:
            continue
        st.write(f"{'+' if term['contribution'] >= 0 else '-'} {label}: {term['contribution']:+.1f}")

    st.markdown(f"**Final score: {score:.1f}**")
