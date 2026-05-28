"""Streamlit rendering for pairwise interaction summaries."""

from __future__ import annotations

from typing import Any

import streamlit as st

from reasoning.explain import render_explanation, render_rationale


def render_pair_summary(
    facts: Any,
    pair_reports: list[Any],
    templates: dict[str, str],
) -> None:
    """Render pairwise interaction summaries and rule-level details."""
    st.subheader("Pair Summary")

    if not pair_reports:
        st.info(
            "No rule-based interactions detected in selected domains "
            "(educational scope)."
        )
        st.stop()

    for report in pair_reports:
        _render_pair_report(facts, report, templates)


def _render_pair_report(
    facts: Any,
    report: Any,
    templates: dict[str, str],
) -> None:
    drug_1 = facts.drugs[report.drug_1].generic_name
    drug_2 = facts.drugs[report.drug_2].generic_name
    title = (
        f"{drug_1} + {drug_2} | "
        f"severity={report.overall_severity.value} | "
        f"class={report.overall_rule_class.value}"
    )

    with st.expander(title, expanded=False):
        _render_pk_hits(facts, report, templates)
        _render_pd_hits(facts, report, templates)
        _render_rule_references(report)


def _render_pk_hits(
    facts: Any,
    report: Any,
    templates: dict[str, str],
) -> None:
    if not report.pk_hits:
        return

    st.markdown("### PK section (directional)")

    if report.pk_summary:
        st.write(f"PK summary: {report.pk_summary}")

    for hit in report.pk_hits:
        st.write(
            f"- [{hit.severity.value} | {hit.rule_class.value}] {hit.name}"
        )

        affected = facts.drugs[hit.inputs["A"]].generic_name
        interacting = facts.drugs[hit.inputs["B"]].generic_name
        st.write(f"  Affected: {affected} | Interacting: {interacting}")

        _render_hit_explanation(facts, hit, templates)
        _render_hit_rationale(facts, hit)
        _render_hit_actions(hit)


def _render_pd_hits(
    facts: Any,
    report: Any,
    templates: dict[str, str],
) -> None:
    if not report.pd_hits:
        return

    st.markdown("### PD section (shared domain)")

    for hit in report.pd_hits:
        st.write(
            f"- [{hit.severity.value} | {hit.rule_class.value}] {hit.name}"
        )

        _render_hit_explanation(facts, hit, templates)
        _render_hit_rationale(facts, hit)
        _render_hit_actions(hit)


def _render_hit_explanation(
    facts: Any,
    hit: Any,
    templates: dict[str, str],
) -> None:
    template = templates.get(hit.rule_id, "")

    if not template:
        return

    st.write("  Explanation:")
    st.write(render_explanation(template, facts, hit))


def _render_hit_rationale(facts: Any, hit: Any) -> None:
    rationale = render_rationale(facts, hit)

    if not rationale:
        return

    st.write("  Rationale:")
    st.code(rationale)


def _render_hit_actions(hit: Any) -> None:
    if not hit.actions:
        return

    st.write("  Suggested actions:")
    for action in hit.actions:
        st.write(f"  - {action}")


def _render_rule_references(report: Any) -> None:
    references = []
    for hit in (report.pk_hits or []) + (report.pd_hits or []):
        references.extend(hit.references or [])

    unique_references = {
        (
            reference.get("source", ""),
            reference.get("citation", ""),
            reference.get("url", ""),
        )
        for reference in references
    }

    if not unique_references:
        return

    st.markdown("### References (rule-level)")
    for source, citation, url in sorted(unique_references):
        if url:
            st.write(f"- {source}: {citation} ({url})")
        else:
            st.write(f"- {source}: {citation}")