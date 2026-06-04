"""Aggregate-level evidence summaries.

This module summarizes evidence trace metadata across aggregate concern
members. It does not change rule hits, scoring, severity, or clinical output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.mechanisms.aggregation import AggregateConcern

EVIDENCE_STATUS_COMPLETE = "complete"
EVIDENCE_STATUS_PARTIAL = "partial"
EVIDENCE_STATUS_MISSING = "missing"
EVIDENCE_STATUS_DISPUTED = "disputed"
EVIDENCE_STATUS_CONFLICTING = "conflicting"
EVIDENCE_STATUS_UNDETERMINED = "undetermined"
EVIDENCE_STATUS_NOT_APPLICABLE = "not_applicable"

DRUG_EVIDENCE_STATUS_PRESENT = "present"
EVIDENCE_CONFLICT_REASON_CLAIM_DISAGREEMENT = "claim_disagreement"
EVIDENCE_CONFLICT_REASON_CONFIDENCE = "confidence"
EVIDENCE_CONFLICT_REASON_COVERAGE = "coverage"
EVIDENCE_CONFLICT_REASON_SOURCE_MISMATCH = "source_mismatch"

LOW_CONFIDENCE_LEVELS = {"low", "uncertain"}
CONFLICTING_CLAIM_STATUSES = {
    EVIDENCE_STATUS_CONFLICTING,
    EVIDENCE_STATUS_DISPUTED,
}
LIMITED_COVERAGE_STATUSES = {
    EVIDENCE_STATUS_PARTIAL,
    EVIDENCE_STATUS_MISSING,
    EVIDENCE_STATUS_UNDETERMINED,
}


@dataclass(frozen=True)
class AggregateEvidenceSummary:
    """Evidence summary for one aggregate concern."""

    aggregate: AggregateConcern
    overall_evidence_status: str = EVIDENCE_STATUS_NOT_APPLICABLE
    evidence_trace_count: int = 0
    evidence_trace_types: tuple[str, ...] = ()
    evidence_effect_ids: tuple[str, ...] = ()
    evidence_statuses: tuple[str, ...] = ()
    evidence_gap_count: int = 0
    evidence_claim_count: int = 0
    evidence_source_ids: tuple[str, ...] = ()
    evidence_source_types: tuple[str, ...] = ()
    evidence_conflict_reasons: tuple[str, ...] = ()
    member_without_evidence_trace_count: int = 0

    @property
    def key(self) -> tuple[str, str, str | None]:
        """Stable dedupe key based on the wrapped aggregate concern."""
        return self.aggregate.key


def summarize_aggregate_evidence(
    aggregates: list[AggregateConcern],
) -> list[AggregateEvidenceSummary]:
    """Summarize evidence metadata for aggregate concerns."""
    summaries = [
        aggregate_to_evidence_summary(aggregate)
        for aggregate in aggregates
    ]

    return dedupe_aggregate_evidence_summaries(summaries)


def aggregate_to_evidence_summary(
    aggregate: AggregateConcern,
) -> AggregateEvidenceSummary:
    """Build one AggregateEvidenceSummary."""
    traces = _evidence_traces_for_aggregate(aggregate)

    if not traces:
        return AggregateEvidenceSummary(
            aggregate=aggregate,
            member_without_evidence_trace_count=len(aggregate.members),
        )

    trace_statuses = tuple(
        sorted(
            {
                _trace_status(trace)
                for trace in traces
            }
        )
    )
    evidence_trace_types = tuple(
        sorted(
            {
                trace_type
                for trace in traces
                if (trace_type := _string_value(trace, "trace_type"))
            }
        )
    )
    evidence_effect_ids = tuple(
        sorted(
            {
                effect_id
                for trace in traces
                if (effect_id := _string_value(trace, "effect_id"))
            }
        )
    )

    return AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=_overall_status(trace_statuses),
        evidence_trace_count=len(traces),
        evidence_trace_types=evidence_trace_types,
        evidence_effect_ids=evidence_effect_ids,
        evidence_statuses=trace_statuses,
        evidence_gap_count=_evidence_gap_count(traces),
        evidence_claim_count=_evidence_claim_count(traces),
        evidence_source_ids=_evidence_source_ids(traces),
        evidence_source_types=_evidence_source_types(traces),
        evidence_conflict_reasons=_evidence_conflict_reasons(
            traces,
            aggregate,
            trace_statuses,
        ),
        member_without_evidence_trace_count=(
            _member_without_evidence_trace_count(aggregate)
        ),
    )


def _evidence_traces_for_aggregate(
    aggregate: AggregateConcern,
) -> list[dict[str, Any]]:
    traces = []

    for member in aggregate.members:
        trace = member.metadata.get("evidence_trace")

        if isinstance(trace, dict):
            traces.append(trace)

    return traces


def _member_without_evidence_trace_count(
    aggregate: AggregateConcern,
) -> int:
    count = 0

    for member in aggregate.members:
        if not isinstance(member.metadata.get("evidence_trace"), dict):
            count += 1

    return count


def _trace_status(trace: dict[str, Any]) -> str:
    status = trace.get("overall_evidence_status")

    if isinstance(status, str) and status:
        return status

    return EVIDENCE_STATUS_UNDETERMINED


def _overall_status(statuses: tuple[str, ...]) -> str:
    status_set = set(statuses)

    if not status_set:
        return EVIDENCE_STATUS_NOT_APPLICABLE

    if EVIDENCE_STATUS_CONFLICTING in status_set:
        return EVIDENCE_STATUS_CONFLICTING

    if EVIDENCE_STATUS_PARTIAL in status_set:
        return EVIDENCE_STATUS_PARTIAL

    if EVIDENCE_STATUS_DISPUTED in status_set:
        return EVIDENCE_STATUS_DISPUTED

    if EVIDENCE_STATUS_MISSING in status_set:
        return EVIDENCE_STATUS_MISSING

    if status_set == {EVIDENCE_STATUS_COMPLETE}:
        return EVIDENCE_STATUS_COMPLETE

    return EVIDENCE_STATUS_UNDETERMINED


def _evidence_gap_count(traces: list[dict[str, Any]]) -> int:
    count = 0

    for trace in traces:
        for item in trace.get("drugs", []) or []:
            if not isinstance(item, dict):
                continue

            if item.get("evidence_status") != DRUG_EVIDENCE_STATUS_PRESENT:
                count += 1

    return count


def _evidence_claim_count(traces: list[dict[str, Any]]) -> int:
    count = 0

    for trace in traces:
        for item in trace.get("drugs", []) or []:
            if not isinstance(item, dict):
                continue

            claims = item.get("claims", []) or []

            if isinstance(claims, list):
                count += len(
                    [
                        claim
                        for claim in claims
                        if isinstance(claim, dict)
                    ]
                )

    return count


def _evidence_source_ids(
    traces: list[dict[str, Any]],
) -> tuple[str, ...]:
    source_ids = set()

    for trace in traces:
        for item in trace.get("drugs", []) or []:
            if not isinstance(item, dict):
                continue

            for claim in item.get("claims", []) or []:
                if not isinstance(claim, dict):
                    continue

                for evidence in claim.get("evidence", []) or []:
                    if not isinstance(evidence, dict):
                        continue

                    source_id = _evidence_source_id(evidence)
                    if source_id:
                        source_ids.add(source_id)

    return tuple(sorted(source_ids))
def _evidence_source_types(
    traces: list[dict[str, Any]],
) -> tuple[str, ...]:
    source_types = set()

    for evidence in _iter_evidence_items(traces):
        source_type = evidence.get("source_type")

        if isinstance(source_type, str) and source_type:
            source_types.add(source_type)

        source = evidence.get("source")
        if isinstance(source, dict):
            nested_source_type = source.get("source_type")
            if isinstance(nested_source_type, str) and nested_source_type:
                source_types.add(nested_source_type)

    return tuple(sorted(source_types))


def _evidence_conflict_reasons(
    traces: list[dict[str, Any]],
    aggregate: AggregateConcern,
    trace_statuses: tuple[str, ...],
) -> tuple[str, ...]:
    reasons = set()

    if _has_claim_disagreement(traces):
        reasons.add(EVIDENCE_CONFLICT_REASON_CLAIM_DISAGREEMENT)

    if _has_confidence_limitation(traces):
        reasons.add(EVIDENCE_CONFLICT_REASON_CONFIDENCE)

    if _has_coverage_limitation(aggregate, trace_statuses, traces):
        reasons.add(EVIDENCE_CONFLICT_REASON_COVERAGE)

    if len(_evidence_source_types(traces)) > 1:
        reasons.add(EVIDENCE_CONFLICT_REASON_SOURCE_MISMATCH)

    return tuple(sorted(reasons))


def _has_claim_disagreement(traces: list[dict[str, Any]]) -> bool:
    for drug in _iter_drug_items(traces):
        if drug.get("evidence_status") in CONFLICTING_CLAIM_STATUSES:
            return True

    for claim in _iter_claim_items(traces):
        if claim.get("evidence_support_status") in CONFLICTING_CLAIM_STATUSES:
            return True

        counts = claim.get("evidence_support_counts")
        if not isinstance(counts, dict):
            continue

        supporting = counts.get("supporting", 0) or 0
        disputing = counts.get("disputing", 0) or 0

        if supporting > 0 and disputing > 0:
            return True

    return False


def _has_confidence_limitation(traces: list[dict[str, Any]]) -> bool:
    for claim in _iter_claim_items(traces):
        confidence = claim.get("evidence_confidence")
        if not isinstance(confidence, dict):
            continue

        level = confidence.get("level")
        if isinstance(level, str) and level in LOW_CONFIDENCE_LEVELS:
            return True

    return False


def _has_coverage_limitation(
    aggregate: AggregateConcern,
    trace_statuses: tuple[str, ...],
    traces: list[dict[str, Any]],
) -> bool:
    if _member_without_evidence_trace_count(aggregate):
        return True

    if set(trace_statuses).intersection(LIMITED_COVERAGE_STATUSES):
        return True

    for drug in _iter_drug_items(traces):
        if drug.get("evidence_status") != DRUG_EVIDENCE_STATUS_PRESENT:
            return True

    return False


def _iter_drug_items(traces: list[dict[str, Any]]):
    for trace in traces:
        for item in trace.get("drugs", []) or []:
            if isinstance(item, dict):
                yield item


def _iter_claim_items(traces: list[dict[str, Any]]):
    for drug in _iter_drug_items(traces):
        for claim in drug.get("claims", []) or []:
            if isinstance(claim, dict):
                yield claim


def _iter_evidence_items(traces: list[dict[str, Any]]):
    for claim in _iter_claim_items(traces):
        for evidence in claim.get("evidence", []) or []:
            if isinstance(evidence, dict):
                yield evidence

def _evidence_source_id(evidence: dict[str, Any]) -> str | None:
    source_id = evidence.get("source_id")
    if isinstance(source_id, str) and source_id:
        return source_id

    source = evidence.get("source")
    if isinstance(source, dict):
        nested_source_id = source.get("source_id")
        if isinstance(nested_source_id, str) and nested_source_id:
            return nested_source_id

    return None

def _string_value(
    item: dict[str, Any],
    key: str,
) -> str | None:
    value = item.get(key)

    if isinstance(value, str) and value:
        return value

    return None


def dedupe_aggregate_evidence_summaries(
    summaries: list[AggregateEvidenceSummary],
) -> list[AggregateEvidenceSummary]:
    """Deduplicate aggregate evidence summaries preserving first-seen order."""
    seen: set[tuple[str, str, str | None]] = set()
    out: list[AggregateEvidenceSummary] = []

    for summary in summaries:
        if summary.key in seen:
            continue

        seen.add(summary.key)
        out.append(summary)

    return out