"""Streamlit rendering for pairwise interaction summaries."""

from __future__ import annotations

from typing import Any

import streamlit as st

from reasoning.explain import render_explanation, render_rationale


def _enum_value(value: Any) -> str:
    """Return enum values without assuming every field is an enum."""
    return getattr(value, "value", str(value))


def _hit_count_label(pk_count: int, pd_count: int) -> str:
    parts = []

    if pk_count:
        parts.append(f"{pk_count} PK")

    if pd_count:
        parts.append(f"{pd_count} PD")

    if not parts:
        return "no hits"

    return ", ".join(parts)


def render_pair_summary(
    facts: Any,
    pair_reports: list[Any],
    templates: dict[str, str],
) -> None:
    """Render pairwise interaction summaries and rule-level details."""
    st.subheader("Pairwise Details")
    st.caption(
        "Pairwise rule details are collapsed by default so the public and "
        "regimen-level summaries stay easier to scan."
    )

    if not pair_reports:
        st.info(
            "No rule-based interactions detected in selected domains "
            "(educational scope)."
        )
        return

    st.caption(f"Pairwise reports: {len(pair_reports)}")

    for report in pair_reports:
        _render_pair_report(facts, report, templates)


def _render_pair_report(
    facts: Any,
    report: Any,
    templates: dict[str, str],
) -> None:
    drug_1 = facts.drugs[report.drug_1].generic_name
    drug_2 = facts.drugs[report.drug_2].generic_name
    pk_count = len(report.pk_hits or [])
    pd_count = len(report.pd_hits or [])
    title = (
        f"{drug_1} + {drug_2} | "
        f"{_enum_value(report.overall_severity)} | "
        f"{_enum_value(report.overall_rule_class)} | "
        f"{_hit_count_label(pk_count, pd_count)}"
    )

    with st.expander(title, expanded=False):
        _render_pair_overview(report, pk_count, pd_count)
        _render_pk_hits(facts, report, templates)
        _render_pd_hits(facts, report, templates)
        _render_rule_references(report)


def _render_pair_overview(report: Any, pk_count: int, pd_count: int) -> None:
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Severity", _enum_value(report.overall_severity))
    col_b.metric("Class", _enum_value(report.overall_rule_class))
    col_c.metric("PK hits", pk_count)
    col_d.metric("PD hits", pd_count)


def _render_pk_hits(
    facts: Any,
    report: Any,
    templates: dict[str, str],
) -> None:
    if not report.pk_hits:
        return

    st.markdown("### Pharmacokinetic (PK) hits")

    if report.pk_summary:
        st.write(report.pk_summary)

    for hit in report.pk_hits:
        with st.container(border=True):
            st.markdown(f"**{hit.name}**")
            st.caption(
                f"Severity: {_enum_value(hit.severity)} | "
                f"Class: {_enum_value(hit.rule_class)}"
            )

            affected = facts.drugs[hit.inputs["A"]].generic_name
            interacting = facts.drugs[hit.inputs["B"]].generic_name
            st.caption(f"Affected: {affected} | Interacting: {interacting}")

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

    st.markdown("### Pharmacodynamic (PD) hits")

    for hit in report.pd_hits:
        with st.container(border=True):
            st.markdown(f"**{hit.name}**")
            st.caption(
                f"Severity: {_enum_value(hit.severity)} | "
                f"Class: {_enum_value(hit.rule_class)}"
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

    st.write("Explanation:")
    st.write(render_explanation(template, facts, hit))


def _render_hit_rationale(facts: Any, hit: Any) -> None:
    rationale = render_rationale(facts, hit)

    if not rationale:
        return

    with st.expander("Rule rationale", expanded=False):
        st.code(rationale)


def _render_hit_actions(hit: Any) -> None:
    if not hit.actions:
        return

    with st.expander("Suggested educational actions", expanded=False):
        for action in hit.actions:
            st.write(f"- {action}")


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

    with st.expander("Rule-level references", expanded=False):
        for source, citation, url in sorted(unique_references):
            if url:
                st.write(f"- {source}: {citation} ({url})")
            else:
                st.write(f"- {source}: {citation}")