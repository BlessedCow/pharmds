"""Streamlit rendering for debug-only mechanism payload details."""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.mechanisms.debug import (
    DEBUG_MECHANISM_PIPELINE_LABEL,
    format_debug_section_title,
)


def mechanism_debug_expander_label() -> str:
    """Return the Streamlit label for mechanism-only debug JSON."""
    return format_debug_section_title(
        DEBUG_MECHANISM_PIPELINE_LABEL,
        "Full JSON",
    )


def mechanism_debug_json_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return only the mechanism pipeline JSON for debug rendering."""
    value = payload.get("mechanism_pipeline_json", {})
    return value if isinstance(value, dict) else {}


def render_mechanism_debug_json(payload: dict[str, Any]) -> None:
    """Render the full mechanism pipeline JSON as lower-priority debug UI."""
    st.subheader("Developer Debug")

    with st.expander(mechanism_debug_expander_label(), expanded=False):
        if st.checkbox(
            "Display raw JSON payload",
            value=False,
            key="debug_mechanism_json",
        ):
            st.json(mechanism_debug_json_payload(payload))