"""Streamlit rendering for debug-only mechanism payload details."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_mechanism_debug_json(payload: dict[str, Any]) -> None:
    """Render the full mechanism pipeline JSON as lower-priority debug UI."""
    st.subheader("Developer Debug")

    with st.expander("Show full mechanism pipeline JSON", expanded=False):
        if st.checkbox(
            "Display raw JSON payload",
            value=False,
            key="debug_mechanism_json",
        ):
            st.json(payload.get("mechanism_pipeline_json", {}))