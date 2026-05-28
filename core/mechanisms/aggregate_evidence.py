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