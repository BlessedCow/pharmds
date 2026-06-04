"""Streamlit rendering for regimen-level summary output."""

from __future__ import annotations

from typing import Any

import streamlit as st


def render_regimen_summary(regimen_summary: dict[str, Any] | None) -> None:
    """Render regimen-level summary details when available."""
    if not regimen_summary:
        return

    st.subheader("Regimen Summary (all drugs)")

    st.write(
        f"Overall: severity={regimen_summary['overall_severity'].value} | "
        f"class={regimen_summary['overall_rule_class'].value}"
    )

    overview = regimen_summary.get("overview")
    if overview:
        st.caption(overview)

    pairwise_summary = regimen_summary.get("pairwise_summary")
    if pairwise_summary:
        st.write(pairwise_summary)

    cumulative_summary = regimen_summary.get("cumulative_concern_summary")
    if cumulative_summary:
        st.write(cumulative_summary)

    hit_counts = regimen_summary.get("hit_counts", {})
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Drugs", regimen_summary.get("n_drugs", 0))
    col_b.metric("Pairs with hits", regimen_summary.get("pair_count_with_hits", 0))
    col_c.metric("Pairwise hits", hit_counts.get("total", 0))

    st.caption(
        f"PK hits: {hit_counts.get('pk', 0)} | "
        f"PD hits: {hit_counts.get('pd', 0)}"
    )

    flags = regimen_summary.get("regimen_flags", [])
    if flags:
        st.warning("Regimen-wide educational flags")
        for flag in flags:
            st.write(f"- {flag.get('message', '')}")

    pd_stacks = regimen_summary.get("pd_stacks", [])
    if pd_stacks:
        st.markdown("### Regimen-wide repeated PD concern domains")
        for stack in pd_stacks[:5]:
            drug_names = ", ".join(
                drug["drug_name"] for drug in stack.get("drugs", [])
            )
            st.write(
                f"- **{stack['label']}**: {stack['count']} drugs "
                f"(max={stack['max_magnitude']}) - {drug_names}"
            )

    top_pairs = regimen_summary.get("top_pairs", [])
    if top_pairs:
        st.markdown("### Pairwise concern highlights")
        for pair in top_pairs[:3]:
            st.write(
                f"- **{pair['drug_1']['name']} + {pair['drug_2']['name']}**: "
                f"{pair['severity']} | {pair['class']} "
                f"({pair['total_hits']} hits)"
            )