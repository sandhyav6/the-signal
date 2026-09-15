"""frontend/pages/preferences.py — Preferences: manual per-category interest
sliders (0-1), Save button -> PUT /preferences (Part 14).
"""

import streamlit as st

from frontend import api_client


def render() -> None:
    st.header("⚙️ Preferences")
    categories = api_client.get_categories()
    if not categories:
        st.info("No categories found.")
        return

    current = api_client.get_preferences(api_client.DEFAULT_USER_ID)
    st.write("Adjust how interested you are in each category (0 = not interested, 1 = very interested).")

    sliders = {}
    for cat in categories:
        current_weight = float(current.get(str(cat["id"]), 0.1))
        sliders[cat["id"]] = st.slider(cat["name"], 0.0, 1.0, current_weight, 0.05, key=f"pref-{cat['id']}")

    if st.button("Save preferences"):
        updates = {str(cid): weight for cid, weight in sliders.items()}
        result = api_client.put_preferences(api_client.DEFAULT_USER_ID, updates)
        if result:
            st.success("Preferences updated — your feed will reflect this on next refresh.")
