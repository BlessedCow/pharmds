"""Combined aggregate concern summaries.

This module joins aggregate concerns with their aggregate-level severity and
evidence summaries.

It does not create new clinical recommendations. It only provides a cleaner
read-only structure for JSON/debug/UI rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from core.mechanisms.aggregate_evidence import (
    EVIDENCE_CONFLICT_REASON_CLAIM_DISAGREEMENT,
    EVIDENCE_CONFLICT_REASON_CONFIDENCE,
    EVIDENCE_CONFLICT_REASON_COVERAGE,
    EVIDENCE_CONFLICT_REASON_SOURCE_MISMATCH,
    EVIDENCE_STATUS_COMPLETE,
    EVIDENCE_STATUS_CONFLICTING,
    EVIDENCE_STATUS_DISPUTED,
    EVIDENCE_STATUS_MISSING,
    EVIDENCE_STATUS_PARTIAL,
    AggregateEvidenceSummary,
)
from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_DECREASE,
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AggregateConcern,
)
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
EVIDENCE_CONFLICT_LEVEL_NONE = "none"
EVIDENCE_CONFLICT_LEVEL_DISPUTED = "disputed"
EVIDENCE_CONFLICT_LEVEL_CONFLICTING = "conflicting"
EVIDENCE_CONFLICT_REASON_LABELS = {
    EVIDENCE_CONFLICT_REASON_CLAIM_DISAGREEMENT: "claim disagreement",
    EVIDENCE_CONFLICT_REASON_CONFIDENCE: "confidence limitations",
    EVIDENCE_CONFLICT_REASON_COVERAGE: "coverage gaps",
    EVIDENCE_CONFLICT_REASON_SOURCE_MISMATCH: "mixed source types",
}

@dataclass(frozen=True)
class AggregateConcernSummary:
    """Combined summary for one aggregate concern."""

    aggregate: AggregateConcern
    severity_annotation: AggregateSeverityAnnotation | None = None
    evidence_summary: AggregateEvidenceSummary | None = None
    patient_risk_modifiers: tuple[str, ...] = ()
    risk_context: str | None = None
    evidence_conflict_level: str = EVIDENCE_CONFLICT_LEVEL_NONE
    evidence_conflict_message: str | None = None
    evidence_conflict_source_ids: tuple[str, ...] = ()
    evidence_conflict_trace_types: tuple[str, ...] = ()
    evidence_conflict_reasons: tuple[str, ...] = ()
    narrative: str = ""

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
        evidence_summary = evidence_by_key.get(aggregate.key)
        (
            conflict_level,
            conflict_message,
            conflict_source_ids,
            conflict_trace_types,
            conflict_reasons,
        ) = summarize_evidence_conflict_surface(evidence_summary)

        summary = AggregateConcernSummary(
            aggregate=aggregate,
            severity_annotation=severity_by_key.get(aggregate.key),
            evidence_summary=evidence_summary,
            patient_risk_modifiers=modifiers,
            risk_context=risk_context,
            evidence_conflict_level=conflict_level,
            evidence_conflict_message=conflict_message,
            evidence_conflict_source_ids=conflict_source_ids,
            evidence_conflict_trace_types=conflict_trace_types,
            evidence_conflict_reasons=conflict_reasons,
        )
        summaries.append(
            replace(
                summary,
                narrative=build_aggregate_summary_narrative(summary),
            )
        )

    return rank_aggregate_concern_summaries(
        dedupe_aggregate_concern_summaries(summaries)
    )

def _aggregate_evidence_conflict_narrative(
    summary: AggregateConcernSummary,
) -> str:
    if not summary.evidence_conflict_message:
        return ""

    return summary.evidence_conflict_message

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

def summarize_evidence_conflict_surface(
    evidence: AggregateEvidenceSummary | None,
) -> tuple[
    str,
    str | None,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    """Return human-readable conflict/dispute context for aggregate evidence."""
    if not evidence:
        return EVIDENCE_CONFLICT_LEVEL_NONE, None, (), (), ()

    if evidence.overall_evidence_status == EVIDENCE_STATUS_CONFLICTING:
        return (
            EVIDENCE_CONFLICT_LEVEL_CONFLICTING,
            (
                "Conflicting curated evidence is attached to this aggregate "
                "concern and should be reviewed separately instead of being "
                "treated as complete support."
                + _evidence_reason_sentence(
                    evidence.evidence_conflict_reasons,
                    prefix="Conflict indicator(s)",
                )
            ),
            evidence.evidence_source_ids,
            evidence.evidence_trace_types,
            evidence.evidence_conflict_reasons,
        )

    if evidence.overall_evidence_status == EVIDENCE_STATUS_DISPUTED:
        return (
            EVIDENCE_CONFLICT_LEVEL_DISPUTED,
            (
                "Disputed curated evidence is attached to this aggregate "
                "concern and should be reviewed separately."
                + _evidence_reason_sentence(
                    evidence.evidence_conflict_reasons,
                    prefix="Dispute indicator(s)",
                )
            ),
            evidence.evidence_source_ids,
            evidence.evidence_trace_types,
            evidence.evidence_conflict_reasons,
        )

    return (
        EVIDENCE_CONFLICT_LEVEL_NONE,
        None,
        (),
        (),
        evidence.evidence_conflict_reasons,
    )

def build_aggregate_summary_narrative(
    summary: AggregateConcernSummary,
) -> str:
    """Build a short educational narrative for an aggregate summary.

    The narrative is intentionally conservative. It explains the grouped
    mechanism, evidence status, and preliminary severity without making
    treatment recommendations.
    """
    aggregate = summary.aggregate
    mechanism_text = _aggregate_mechanism_narrative(aggregate)
    evidence_text = _aggregate_evidence_narrative(summary)
    severity_text = _aggregate_severity_narrative(summary)
    conflict_text = _aggregate_evidence_conflict_narrative(summary)
    risk_text = _aggregate_patient_risk_narrative(summary)

    parts = [
        mechanism_text,
        evidence_text,
        severity_text,
    ]

    if conflict_text:
        parts.append(conflict_text)

    if risk_text:
        parts.append(risk_text)

    parts.append("This explanation is educational and not diagnostic.")

    return " ".join(part for part in parts if part)


def _aggregate_mechanism_narrative(
    aggregate: AggregateConcern,
) -> str:
    drugs = _human_join(aggregate.drugs)

    if aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT:
        effect_id = aggregate.effect_id or aggregate.anchor
        return (
            f"{drugs} share a {effect_id}-related pharmacodynamic effect."
        )

    if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_INCREASE:
        targets = _human_join(aggregate.targets)
        target_text = (
            f" through {targets}-related mechanism(s)"
            if targets
            else ""
        )
        return (
            f"{drugs} include mechanism(s) that may increase "
            f"{aggregate.anchor} exposure{target_text}."
        )

    if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_DECREASE:
        targets = _human_join(aggregate.targets)
        target_text = (
            f" through {targets}-related mechanism(s)"
            if targets
            else ""
        )
        return (
            f"{drugs} include mechanism(s) that may decrease "
            f"{aggregate.anchor} exposure{target_text}."
        )

    if aggregate.effect_id:
        return (
            f"{drugs} are grouped around {aggregate.effect_id} "
            f"as a {aggregate.policy_concern}."
        )

    return (
        f"{drugs} are grouped as a {aggregate.policy_concern}."
    )


def _aggregate_evidence_narrative(
    summary: AggregateConcernSummary,
) -> str:
    evidence = summary.evidence_summary

    if not evidence:
        return "No aggregate-level evidence summary is attached."

    evidence_label = _evidence_status_label(
        evidence.overall_evidence_status,
    )

    limitation_text = ""

    if (
        evidence.evidence_conflict_reasons
        and summary.evidence_conflict_level == EVIDENCE_CONFLICT_LEVEL_NONE
    ):
        limitation_text = _evidence_reason_sentence(
            evidence.evidence_conflict_reasons,
            prefix="Evidence limitation indicator(s)",
        )

    return f"This grouped concern has {evidence_label}.{limitation_text}"


def _aggregate_severity_narrative(
    summary: AggregateConcernSummary,
) -> str:
    severity = summary.severity_annotation

    if not severity or not severity.strongest_preliminary_severity:
        return "It does not have a preliminary severity classification."

    return (
        "It is preliminarily classified as "
        f"{severity.strongest_preliminary_severity}-level."
    )


def _aggregate_patient_risk_narrative(
    summary: AggregateConcernSummary,
) -> str:
    if not summary.patient_risk_modifiers:
        return ""

    modifiers = _human_join(summary.patient_risk_modifiers)
    context = summary.risk_context or ""

    if context:
        return f"Patient risk modifier(s) present: {modifiers}. {context}"

    return f"Patient risk modifier(s) present: {modifiers}."

def _evidence_reason_sentence(
    reasons: tuple[str, ...],
    *,
    prefix: str,
) -> str:
    if not reasons:
        return ""

    labels = tuple(
        _evidence_reason_label(reason)
        for reason in reasons
    )

    return f" {prefix}: {_human_join(labels)}."


def _evidence_reason_label(reason: str) -> str:
    return EVIDENCE_CONFLICT_REASON_LABELS.get(
        reason,
        reason.replace("_", " "),
    )

def _evidence_status_label(status: str) -> str:
    labels = {
        EVIDENCE_STATUS_COMPLETE: "complete curated evidence support",
        EVIDENCE_STATUS_PARTIAL: "partial curated evidence support",
        EVIDENCE_STATUS_MISSING: "missing curated evidence support",
        EVIDENCE_STATUS_DISPUTED: "disputed curated evidence context",
        EVIDENCE_STATUS_CONFLICTING: "conflicting curated evidence context",
        "not_applicable": "no aggregate-level curated evidence requirement",
        "undetermined": "undetermined curated evidence support",
    }

    return labels.get(status, f"{status} evidence status")


def _human_join(items: tuple[str, ...]) -> str:
    if not items:
        return "No selected drugs"

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{', '.join(items[:-1])}, and {items[-1]}"

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