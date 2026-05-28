"""Streamlit input controls for the main PharmDS app."""

from __future__ import annotations

import streamlit as st

DEFAULT_DOMAIN = "all"


def reset_analysis_state() -> None:
    """Clear user inputs and cached analysis output."""
    st.session_state["drug_text"] = ""
    st.session_state["qt_risk"] = False
    st.session_state["bleeding_risk"] = False
    st.session_state["domain"] = DEFAULT_DOMAIN
    st.session_state["debug_mechanism_json"] = False
    st.session_state["analysis_result"] = None


def render_analysis_controls() -> tuple[str, bool, bool, str, bool]:
    """Render main input controls and return current UI state."""
    st.button("Reset", on_click=reset_analysis_state)

    drug_text = st.text_area(
        "Drugs (one per line, or comma/space separated)",
        height=140,
        placeholder="quetiapine\nclarithromycin",
        key="drug_text",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        qt_risk = st.checkbox("QT risk factors", value=False, key="qt_risk")
    with col2:
        bleeding_risk = st.checkbox(
            "Bleeding risk factors",
            value=False,
            key="bleeding_risk",
        )
    with col3:
        domain = st.text_input(
            "Domains (e.g. all, pk, pd, cyp, ugt, pgp, bcrp, oatp)",
            value=DEFAULT_DOMAIN,
            key="domain",
        )

    run = st.button("Analyze", type="primary")

    return drug_text, qt_risk, bleeding_risk, domain, run