"""Combined aggregate concern summaries.

This module joins aggregate concerns with their aggregate-level severity and
evidence summaries.

It does not create new clinical recommendations. It only provides a cleaner
read-only structure for JSON/debug/UI rendering.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.aggregate_evidence import (
    EVIDENCE_STATUS_COMPLETE,
    EVIDENCE_STATUS_CONFLICTING,
    EVIDENCE_STATUS_DISPUTED,
    EVIDENCE_STATUS_MISSING,
    EVIDENCE_STATUS_PARTIAL,
    AggregateEvidenceSummary,
)
from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
from core.mechanisms.aggregation import AggregateConcern
from core.mechanisms.policy import POLICY_MECHANISTIC_CONCERN
from core.mechanisms.severity import (
    PRELIMINARY_SEVERITY_CAUTION,
    PRELIMINARY_SEVERITY_HIGH_CAUTION,
    PRELIMINARY_SEVERITY_INFORMATIONAL,
)

AGGREGATE_SUMMARY_SEVERITY_RANKS = {
    PRELIMINARY_SEVERITY_HIGH_CAUTION: 3,
    PRELIMINARY_SEVERITY_CAUTION: 2,
    PRELIMINARY_SEVERITY_INFORMATIONAL: 1,
}

AGGREGATE_SUMMARY_EVIDENCE_RANKS = {
    EVIDENCE_STATUS_CONFLICTING: 4,
    EVIDENCE_STATUS_COMPLETE: 3,
    EVIDENCE_STATUS_PARTIAL: 2,
    EVIDENCE_STATUS_DISPUTED: 1,
    EVIDENCE_STATUS_MISSING: 0,
}

PATIENT_RISK_EFFECT_MAP = {
    "qt_risk": ("QT_prolongation",),
    "bleeding_risk": ("bleeding",),
}

PATIENT_RISK_CONTEXT = {
    "qt_risk": (
        "QT-related concern may be more important when QT risk flag is present."
    ),
    "bleeding_risk": (
        "Bleeding-related concern may be more important when bleeding risk flag "
        "is present."
    ),
}


@dataclass(frozen=True)
class AggregateConcernSummary:
    """Combined summary for one aggregate concern."""

    aggregate: AggregateConcern
    severity_annotation: AggregateSeverityAnnotation | None = None
    evidence_summary: AggregateEvidenceSummary | None = None
    patient_risk_modifiers: tuple[str, ...] = ()
    risk_context: str | None = None

    @property
    def key(self) -> tuple[str, str, str | None]:
        """Stable dedupe key based on the wrapped aggregate concern."""
        return self.aggregate.key


def build_aggregate_concern_summaries(
    aggregates: list[AggregateConcern],
    severity_annotations: list[AggregateSeverityAnnotation],
    evidence_summaries: list[AggregateEvidenceSummary],
    patient_flags: dict[str, bool] | None = None,
) -> list[AggregateConcernSummary]:
    """Join aggregate concerns with severity, evidence, and patient context."""
    severity_by_key = {
        annotation.key: annotation
        for annotation in severity_annotations
    }
    evidence_by_key = {
        summary.key: summary
        for summary in evidence_summaries
    }

    summaries = []

    for aggregate in aggregates:
        modifiers, risk_context = summarize_patient_risk_modifiers(
            aggregate,
            patient_flags or {},
        )
        summaries.append(
            AggregateConcernSummary(
                aggregate=aggregate,
                severity_annotation=severity_by_key.get(aggregate.key),
                evidence_summary=evidence_by_key.get(aggregate.key),
                patient_risk_modifiers=modifiers,
                risk_context=risk_context,
            )
        )

    return rank_aggregate_concern_summaries(
        dedupe_aggregate_concern_summaries(summaries)
    )


def dedupe_aggregate_concern_summaries(
    summaries: list[AggregateConcernSummary],
) -> list[AggregateConcernSummary]:
    """Deduplicate aggregate summaries preserving first-seen order."""
    seen: set[tuple[str, str, str | None]] = set()
    out: list[AggregateConcernSummary] = []

    for summary in summaries:
        if summary.key in seen:
            continue

        seen.add(summary.key)
        out.append(summary)

    return out


def rank_aggregate_concern_summaries(
    summaries: list[AggregateConcernSummary],
) -> list[AggregateConcernSummary]:
    """Rank aggregate summaries by practical importance.

    Ranking is deterministic and stable. More important summaries move toward
    the front, while summaries with equal rank keep their original order.
    """
    return sorted(
        summaries,
        key=aggregate_concern_summary_rank_key,
        reverse=True,
    )


def aggregate_concern_summary_rank_key(
    summary: AggregateConcernSummary,
) -> tuple[int, int, int, int, int]:
    """Return a sortable importance key for one aggregate summary."""
    return (
        _summary_severity_rank(summary),
        _summary_patient_risk_rank(summary),
        _summary_evidence_rank(summary),
        _narrow_therapeutic_index_mechanism_rank(summary),
        len(summary.aggregate.members),
    )


def summarize_patient_risk_modifiers(
    aggregate: AggregateConcern,
    patient_flags: dict[str, bool],
) -> tuple[tuple[str, ...], str | None]:
    """Return relevant patient risk modifiers for one aggregate concern.

    This is educational/debug context only. It does not change final rule
    recommendations or clinical severity.
    """
    if not patient_flags:
        return (), None

    effect_ids = _aggregate_effect_ids(aggregate)
    modifiers = []

    for flag, relevant_effect_ids in PATIENT_RISK_EFFECT_MAP.items():
        if not patient_flags.get(flag):
            continue

        if effect_ids.intersection(relevant_effect_ids):
            modifiers.append(flag)

    if not modifiers:
        return (), None

    contexts = [
        PATIENT_RISK_CONTEXT[modifier]
        for modifier in modifiers
        if modifier in PATIENT_RISK_CONTEXT
    ]

    return tuple(modifiers), " ".join(contexts) if contexts else None


def _aggregate_effect_ids(aggregate: AggregateConcern) -> set[str]:
    effect_ids: set[str] = set()

    if aggregate.effect_id:
        effect_ids.update(_split_effect_ids(aggregate.effect_id))

    for member in aggregate.members:
        if member.effect_id:
            effect_ids.add(member.effect_id)

    return effect_ids


def _split_effect_ids(raw: str) -> set[str]:
    return {
        item.strip()
        for item in raw.split(",")
        if item.strip()
    }


def _summary_severity_rank(summary: AggregateConcernSummary) -> int:
    annotation = summary.severity_annotation

    if not annotation or not annotation.strongest_preliminary_severity:
        return 0

    return AGGREGATE_SUMMARY_SEVERITY_RANKS.get(
        annotation.strongest_preliminary_severity,
        0,
    )


def _summary_patient_risk_rank(summary: AggregateConcernSummary) -> int:
    return 1 if summary.patient_risk_modifiers else 0


def _summary_evidence_rank(summary: AggregateConcernSummary) -> int:
    evidence = summary.evidence_summary

    if not evidence:
        return 0

    return AGGREGATE_SUMMARY_EVIDENCE_RANKS.get(
        evidence.overall_evidence_status,
        0,
    )


def _narrow_therapeutic_index_mechanism_rank(
    summary: AggregateConcernSummary,
) -> int:
    aggregate = summary.aggregate

    if aggregate.policy_concern != POLICY_MECHANISTIC_CONCERN:
        return 0

    for member in aggregate.members:
        if member.metadata.get("object_therapeutic_index") == "narrow":
            return 1
        if member.metadata.get("therapeutic_index") == "narrow":
            return 1

    return 0