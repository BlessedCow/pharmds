"""Streamlit rendering for aggregate/public result summaries."""

from __future__ import annotations

from typing import Any

import streamlit as st

from app.streamlit_ui.summary_helpers import (
    aggregate_summary_debug_lines,
    result_summaries_to_streamlit_cards,
)


def render_public_result_summaries(
    public_result_summaries: list[Any],
    aggregate_concern_summaries: list[Any],
) -> None:
    """Render public aggregate summaries and compact evidence details."""
    cards = result_summaries_to_streamlit_cards(public_result_summaries)

    if not cards:
        return

    st.subheader("Key Interaction Summaries")
    st.caption(
        "Public educational summaries are shown first. "
        "Evidence and mechanism details are available in each expander."
    )

    for card in cards:
        with st.container(border=True):
            st.markdown(f"### {card['title']}")
            st.write(card["explanation"])

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Concern", card["concern_type_label"])
            col_b.metric("Severity", card["severity_display"])
            col_c.metric("Evidence", card["evidence_display"])

            st.caption(f"Drugs: {card['drugs']}")

            summary_index = card.get("summary_index")
            has_aggregate_details = (
                card.get("source") == "aggregate_summary"
                and isinstance(summary_index, int)
                and summary_index < len(aggregate_concern_summaries)
            )

            if has_aggregate_details:
                with st.expander("Show evidence and mechanism details"):
                    for line in aggregate_summary_debug_lines(
                        aggregate_concern_summaries[summary_index]
                    ):
                        st.write(line)