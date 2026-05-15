"""Human-facing evidence rendering helpers.

These helpers intentionally produce compact, secondary evidence text for normal
CLI/UI output. Debug evidence formatting remains in core.evidence.formatting.
"""

from __future__ import annotations

from typing import Any

from core.evidence.pd_interaction_traces import (
    build_additive_pd_effect_evidence_trace,
)
from core.models import Facts, RuleHit

_EVIDENCE_TYPE_LABELS = {
    "internal_curated_entry": "curated PD effect claim",
    "drug_label": "drug label evidence",
    "guideline": "guideline evidence",
    "primary_literature": "primary literature evidence",
    "case_report": "case report evidence",
    "mechanistic_inference": "mechanistic inference",
}


def _display_value(value: object, fallback: str = "unknown") -> str:
    """Return a readable display value for human output."""
    if value is None:
        return fallback

    if value == "":
        return fallback

    return str(value)


def _evidence_type_label(evidence_type: object) -> str:
    """Return a compact label for an evidence type."""
    raw = _display_value(evidence_type)

    return _EVIDENCE_TYPE_LABELS.get(raw, raw.replace("_", " "))


def _first_supporting_evidence(claim: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first evidence item that supports the claim, if present."""
    for evidence in claim.get("evidence", []):
        if not isinstance(evidence, dict):
            continue

        if evidence.get("supports_claim") is True:
            return evidence

    return None


def _format_drug_evidence_line(
    drug_trace: dict[str, Any],
    *,
    drug_names: dict[str, str] | None = None,
) -> str:
    """Return one concise human-facing evidence line for a drug trace."""
    drug_id = _display_value(drug_trace.get("drug_id"), "unknown_drug")
    display_name = (drug_names or {}).get(drug_id, drug_id)
    evidence_status = _display_value(drug_trace.get("evidence_status"))
    claims = drug_trace.get("claims", [])

    if evidence_status != "present" or not claims:
        return f"{display_name}: no approved evidence claim found"

    claim = next(
        (item for item in claims if isinstance(item, dict)),
        None,
    )

    if claim is None:
        return f"{display_name}: no approved evidence claim found"

    evidence = _first_supporting_evidence(claim)

    if evidence is None:
        return f"{display_name}: approved claim present, evidence details unavailable"

    evidence_label = _evidence_type_label(evidence.get("evidence_type"))
    confidence = _display_value(evidence.get("confidence"))

    return f"{display_name}: supported by {evidence_label}, {confidence} confidence"


def format_human_evidence_trace(
    trace: dict[str, Any],
    *,
    drug_names: dict[str, str] | None = None,
) -> list[str]:
    """Return compact human-facing lines for an additive PD evidence trace."""
    overall_status = _display_value(
        trace.get("overall_evidence_status"),
        "unknown",
    )
    drug_traces = trace.get("drugs", [])

    lines = [f"Evidence status: {overall_status}"]

    for drug_trace in drug_traces:
        if not isinstance(drug_trace, dict):
            continue

        lines.append(
            _format_drug_evidence_line(
                drug_trace,
                drug_names=drug_names,
            )
        )

    return lines


def build_human_evidence_lines_for_rule_hit(
    facts: Facts,
    hit: RuleHit,
) -> list[str]:
    """Return compact evidence lines for a PD additive RuleHit.

    Returns an empty list when the hit does not have the needed PD overlap
    inputs. This keeps callers safe to use this on arbitrary RuleHit objects.
    """
    inputs = hit.inputs or {}
    drug_a = inputs.get("A")
    drug_b = inputs.get("B")
    effect_id = inputs.get("effect_id")

    if not isinstance(drug_a, str):
        return []

    if not isinstance(drug_b, str):
        return []

    if not isinstance(effect_id, str):
        return []

    trace = build_additive_pd_effect_evidence_trace(
        [drug_a, drug_b],
        effect_id,
    )
    drug_names = {
        drug_id: drug.generic_name
        for drug_id, drug in facts.drugs.items()
    }

    return format_human_evidence_trace(trace, drug_names=drug_names)