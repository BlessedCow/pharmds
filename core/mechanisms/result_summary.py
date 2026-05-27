"""Public-facing result summaries.

This module converts internal/debug mechanism objects into a smaller
end-user-facing summary shape.

It intentionally avoids exposing pipeline internals such as aggregate members,
evidence traces, arbitration details, policy results, or scored concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.mechanisms.aggregate_summary import AggregateConcernSummary
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_DECREASE,
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
)
from core.mechanisms.pipeline import MechanismPipelineResult
from core.models import PairReport, RuleHit

RESULT_SOURCE_AGGREGATE = "aggregate_summary"
RESULT_SOURCE_RULE = "legacy_rule_hit"

EVIDENCE_LABEL_NOT_AVAILABLE = "not_available"
EVIDENCE_LABEL_LEGACY_RULE = "legacy_rule"

PUBLIC_EFFECT_LABELS = {
    "QT_prolongation": "QT prolongation",
    "h1_antagonism": "antihistamine/sedation-related effect",
    "tachycardia_risk": "increased heart-rate risk",
    "hypertension_risk": "blood-pressure elevation risk",
    "intracranial_hypertension_risk": "intracranial hypertension risk",
    "CNS_depression": "CNS depression",
    "serotonin_syndrome": "serotonin syndrome",
    "seizure_risk": "seizure risk",
    "orthostatic_hypotension": "orthostatic hypotension",
    "anticholinergic_effects": "anticholinergic effects",
    "activation_agitation_risk": "activation/agitation risk",
    "insomnia_risk": "insomnia risk",
    "nausea": "nausea",
    "bleeding": "bleeding risk",
}


@dataclass(frozen=True)
class ResultSummary:
    """Small public summary suitable for future UI/default output."""

    source: str
    title: str
    drugs: tuple[str, ...]
    concern_type: str
    severity_label: str
    evidence_label: str
    explanation: str


def build_public_result_summaries(
    pipeline: MechanismPipelineResult,
    pair_reports: list[PairReport] | None = None,
) -> list[ResultSummary]:
    """Build public summaries from aggregate summaries and legacy rule hits."""
    summaries = [
        aggregate_summary_to_result_summary(summary)
        for summary in pipeline.aggregate_concern_summaries
    ]

    if pair_reports:
        summaries.extend(
            build_legacy_rule_result_summaries(pair_reports)
        )

    return dedupe_result_summaries(summaries)


def aggregate_summary_to_result_summary(
    summary: AggregateConcernSummary,
) -> ResultSummary:
    """Convert one aggregate concern summary into a public result summary."""
    aggregate = summary.aggregate

    return ResultSummary(
        source=RESULT_SOURCE_AGGREGATE,
        title=_aggregate_summary_title(summary),
        drugs=tuple(aggregate.drugs),
        concern_type=aggregate.policy_concern,
        severity_label=_aggregate_severity_label(summary),
        evidence_label=_aggregate_evidence_label(summary),
        explanation=_public_explanation(
            summary.narrative
            or _aggregate_fallback_explanation(summary),
        ),
    )


def build_legacy_rule_result_summaries(
    pair_reports: list[PairReport],
) -> list[ResultSummary]:
    """Convert legacy rule hits into public result summaries."""
    summaries = []

    for report in pair_reports:
        for hit in _pair_report_hits(report):
            summaries.append(
                legacy_rule_hit_to_result_summary(report, hit)
            )

    return summaries


def legacy_rule_hit_to_result_summary(
    report: PairReport,
    hit: RuleHit,
) -> ResultSummary:
    """Convert one legacy rule hit into a public result summary."""
    return ResultSummary(
        source=RESULT_SOURCE_RULE,
        title=hit.name,
        drugs=_legacy_rule_drugs(report, hit),
        concern_type=_value(hit.domain),
        severity_label=_value(hit.severity),
        evidence_label=EVIDENCE_LABEL_LEGACY_RULE,
        explanation=_legacy_rule_explanation(hit),
    )


def result_summary_to_json_dict(summary: ResultSummary) -> dict[str, Any]:
    """Convert a public result summary to a JSON-safe dict."""
    return {
        "source": summary.source,
        "title": summary.title,
        "drugs": list(summary.drugs),
        "concern_type": summary.concern_type,
        "severity_label": summary.severity_label,
        "evidence_label": summary.evidence_label,
        "explanation": summary.explanation,
    }


def result_summaries_to_json_dicts(
    summaries: list[ResultSummary],
) -> list[dict[str, Any]]:
    """Convert public result summaries to JSON-safe dicts."""
    return [
        result_summary_to_json_dict(summary)
        for summary in summaries
    ]


def dedupe_result_summaries(
    summaries: list[ResultSummary],
) -> list[ResultSummary]:
    """Deduplicate public result summaries preserving first-seen order."""
    seen: set[tuple[str, str, tuple[str, ...], str]] = set()
    out = []

    for summary in summaries:
        key = (
            summary.source,
            summary.title,
            summary.drugs,
            summary.concern_type,
        )
        if key in seen:
            continue

        seen.add(key)
        out.append(summary)

    return out


def _aggregate_summary_title(summary: AggregateConcernSummary) -> str:
    aggregate = summary.aggregate

    if aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT:
        effect_id = aggregate.effect_id or aggregate.anchor
        effect_label = _effect_display_label(effect_id)
        return f"Shared {effect_label} concern"

    if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_INCREASE:
        return f"{aggregate.anchor} exposure increase concern"

    if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_DECREASE:
        return f"{aggregate.anchor} exposure decrease concern"

    if aggregate.effect_id:
        effect_label = _effect_display_label(aggregate.effect_id)
        return f"{effect_label} concern"

    return f"{aggregate.policy_concern} concern"


def _effect_display_label(effect_id: str | None) -> str:
    if not effect_id:
        return "unspecified effect"

    return PUBLIC_EFFECT_LABELS.get(effect_id, effect_id.replace("_", " "))


def _public_explanation(explanation: str) -> str:
    out = explanation

    for effect_id in sorted(PUBLIC_EFFECT_LABELS, key=len, reverse=True):
        out = out.replace(effect_id, _effect_display_label(effect_id))

    return out


def _aggregate_severity_label(summary: AggregateConcernSummary) -> str:
    severity = summary.severity_annotation

    if not severity or not severity.strongest_preliminary_severity:
        return "unspecified"

    return str(severity.strongest_preliminary_severity)


def _aggregate_evidence_label(summary: AggregateConcernSummary) -> str:
    evidence = summary.evidence_summary

    if not evidence or not evidence.overall_evidence_status:
        return EVIDENCE_LABEL_NOT_AVAILABLE

    return str(evidence.overall_evidence_status)


def _aggregate_fallback_explanation(
    summary: AggregateConcernSummary,
) -> str:
    aggregate = summary.aggregate
    drugs = _human_join(tuple(aggregate.drugs))

    return (
        f"{drugs} are grouped as a {aggregate.policy_concern}. "
        "This summary is educational and not diagnostic."
    )


def _pair_report_hits(report: PairReport) -> list[RuleHit]:
    return list(report.pk_hits or []) + list(report.pd_hits or [])


def _legacy_rule_drugs(
    report: PairReport,
    hit: RuleHit,
) -> tuple[str, ...]:
    inputs = hit.inputs or {}
    drugs = []

    for key in ("A", "B"):
        value = inputs.get(key)
        if isinstance(value, str) and value:
            drugs.append(value)

    if drugs:
        return tuple(dict.fromkeys(drugs))

    return (report.drug_1, report.drug_2)


def _legacy_rule_explanation(hit: RuleHit) -> str:
    if hit.rationale:
        return " ".join(str(item) for item in hit.rationale if item)

    if hit.actions:
        actions = "; ".join(str(item) for item in hit.actions if item)
        return f"Legacy rule action context: {actions}"

    return "Legacy rule summary. This summary is educational and not diagnostic."


def _human_join(items: tuple[str, ...]) -> str:
    if not items:
        return "The selected drugs"

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _value(item) -> str:
    if hasattr(item, "value"):
        return str(item.value)

    return str(item)