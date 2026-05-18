from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.aggregation import AggregateConcern
from core.mechanisms.policy import ConcernPolicyResult
from core.mechanisms.severity import (
    SeverityAnnotatedConcern,
    strongest_preliminary_severity,
)


@dataclass(frozen=True)
class AggregateSeverityAnnotation:
    """Aggregate concern with summarized preliminary severity context."""

    aggregate: AggregateConcern
    strongest_preliminary_severity: str | None = None
    contributing_preliminary_severities: tuple[str, ...] = ()
    severity_reasons: tuple[str, ...] = ()

    @property
    def key(self) -> tuple[str, str, str | None]:
        """Stable dedupe key based on the wrapped aggregate concern."""
        return self.aggregate.key


def annotate_aggregate_preliminary_severity(
    aggregates: list[AggregateConcern],
    annotations: list[SeverityAnnotatedConcern],
) -> list[AggregateSeverityAnnotation]:
    """Summarize member-level preliminary severity per aggregate concern."""
    annotated = [
        aggregate_to_severity_annotation(aggregate, annotations)
        for aggregate in aggregates
    ]

    return dedupe_aggregate_severity_annotations(annotated)


def aggregate_to_severity_annotation(
    aggregate: AggregateConcern,
    annotations: list[SeverityAnnotatedConcern],
) -> AggregateSeverityAnnotation:
    """Convert one AggregateConcern into an AggregateSeverityAnnotation."""
    matching_annotations = _matching_annotations_for_aggregate(
        aggregate,
        annotations,
    )

    severities = tuple(
        sorted(
            {
                annotation.preliminary_severity
                for annotation in matching_annotations
                if annotation.preliminary_severity
            }
        )
    )
    severity_reasons = tuple(
        sorted(
            {
                annotation.severity_reason
                for annotation in matching_annotations
                if annotation.severity_reason
            }
        )
    )

    return AggregateSeverityAnnotation(
        aggregate=aggregate,
        strongest_preliminary_severity=strongest_preliminary_severity(
            list(severities),
        ),
        contributing_preliminary_severities=severities,
        severity_reasons=severity_reasons,
    )


def _matching_annotations_for_aggregate(
    aggregate: AggregateConcern,
    annotations: list[SeverityAnnotatedConcern],
) -> list[SeverityAnnotatedConcern]:
    member_keys = {_policy_result_key(member) for member in aggregate.members}

    return [
        annotation
        for annotation in annotations
        if annotation.key in member_keys
    ]


def _policy_result_key(
    result: ConcernPolicyResult,
) -> tuple[str, str, str, str | None, str | None]:
    return (
        result.policy_concern,
        result.precipitant_drug,
        result.object_drug,
        result.target,
        result.effect_id,
    )


def dedupe_aggregate_severity_annotations(
    annotations: list[AggregateSeverityAnnotation],
) -> list[AggregateSeverityAnnotation]:
    """Deduplicate aggregate severity annotations preserving first-seen order."""
    seen: set[tuple[str, str, str | None]] = set()
    out: list[AggregateSeverityAnnotation] = []

    for annotation in annotations:
        if annotation.key in seen:
            continue
        seen.add(annotation.key)
        out.append(annotation)

    return out