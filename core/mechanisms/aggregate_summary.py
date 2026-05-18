"""Combined aggregate concern summaries.

This module joins aggregate concerns with their aggregate-level severity and
evidence summaries.

It does not create new clinical recommendations. It only provides a cleaner
read-only structure for JSON/debug/UI rendering.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.aggregate_evidence import AggregateEvidenceSummary
from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
from core.mechanisms.aggregation import AggregateConcern


@dataclass(frozen=True)
class AggregateConcernSummary:
    """Combined summary for one aggregate concern."""

    aggregate: AggregateConcern
    severity_annotation: AggregateSeverityAnnotation | None = None
    evidence_summary: AggregateEvidenceSummary | None = None

    @property
    def key(self) -> tuple[str, str, str | None]:
        """Stable dedupe key based on the wrapped aggregate concern."""
        return self.aggregate.key


def build_aggregate_concern_summaries(
    aggregates: list[AggregateConcern],
    severity_annotations: list[AggregateSeverityAnnotation],
    evidence_summaries: list[AggregateEvidenceSummary],
) -> list[AggregateConcernSummary]:
    """Join aggregate concerns with severity and evidence summaries."""
    severity_by_key = {
        annotation.key: annotation
        for annotation in severity_annotations
    }
    evidence_by_key = {
        summary.key: summary
        for summary in evidence_summaries
    }

    summaries = [
        AggregateConcernSummary(
            aggregate=aggregate,
            severity_annotation=severity_by_key.get(aggregate.key),
            evidence_summary=evidence_by_key.get(aggregate.key),
        )
        for aggregate in aggregates
    ]

    return dedupe_aggregate_concern_summaries(summaries)


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