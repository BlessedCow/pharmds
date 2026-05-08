"""Preliminary severity annotation for scored mechanism concerns.

This module adds a non-final severity annotation layer for mechanism pipeline
debugging and future arbitration work.

It intentionally does not assign final clinical severity or recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.policy import (
    POLICY_EXPOSURE_REDUCTION_CONCERN,
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
)
from core.mechanisms.scoring import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    ScoredConcern,
)

PRELIMINARY_SEVERITY_UNSCORED = "unscored"
PRELIMINARY_SEVERITY_INFORMATIONAL = "informational"
PRELIMINARY_SEVERITY_CAUTION = "caution"
PRELIMINARY_SEVERITY_HIGH_CAUTION = "high_caution"


@dataclass(frozen=True)
class SeverityAnnotatedConcern:
    """Scored concern with a preliminary, non-final severity annotation."""

    scored: ScoredConcern
    preliminary_severity: str = PRELIMINARY_SEVERITY_UNSCORED
    severity_reason: str = ""

    @property
    def key(self) -> tuple[str, str, str, str | None, str | None]:
        """Stable dedupe key based on the wrapped scored concern."""
        return self.scored.key


def annotate_preliminary_severity(
    concerns: list[ScoredConcern],
) -> list[SeverityAnnotatedConcern]:
    """Annotate scored concerns with preliminary non-final severity labels."""
    annotated = [
        scored_concern_to_severity_annotation(concern)
        for concern in concerns
    ]

    return dedupe_severity_annotations(annotated)


def scored_concern_to_severity_annotation(
    concern: ScoredConcern,
) -> SeverityAnnotatedConcern:
    """Convert one ScoredConcern into a SeverityAnnotatedConcern."""
    preliminary_severity, reason = _severity_for_scored_concern(concern)

    return SeverityAnnotatedConcern(
        scored=concern,
        preliminary_severity=preliminary_severity,
        severity_reason=reason,
    )


def _severity_for_scored_concern(
    concern: ScoredConcern,
) -> tuple[str, str]:
    if concern.policy_concern == POLICY_SAFETY_CONCERN:
        if concern.confidence == CONFIDENCE_HIGH:
            return (
                PRELIMINARY_SEVERITY_HIGH_CAUTION,
                "High-confidence safety concern.",
            )
        return (
            PRELIMINARY_SEVERITY_CAUTION,
            "Safety concern without high confidence.",
        )

    if concern.policy_concern == POLICY_MECHANISTIC_CONCERN:
        if concern.aggregate_member_count >= 2:
            return (
                PRELIMINARY_SEVERITY_CAUTION,
                "Multiple mechanism candidates affect the same object drug.",
            )
        if concern.confidence == CONFIDENCE_HIGH:
            return (
                PRELIMINARY_SEVERITY_INFORMATIONAL,
                "Single high-confidence mechanistic concern.",
            )

    if concern.policy_concern == POLICY_EXPOSURE_REDUCTION_CONCERN:
        if concern.aggregate_member_count >= 2:
            return (
                PRELIMINARY_SEVERITY_CAUTION,
                "Multiple exposure-reduction candidates affect the same object drug.",
            )
        return (
            PRELIMINARY_SEVERITY_INFORMATIONAL,
            "Exposure-reduction concern identified.",
        )

    if concern.policy_concern == POLICY_TOLERABILITY_CONCERN:
        if concern.aggregate_member_count >= 2:
            return (
                PRELIMINARY_SEVERITY_CAUTION,
                "Multiple tolerability-related candidates identified.",
            )
        if concern.confidence in {CONFIDENCE_MODERATE, CONFIDENCE_HIGH}:
            return (
                PRELIMINARY_SEVERITY_INFORMATIONAL,
                "Tolerability concern identified.",
            )

    if concern.confidence == CONFIDENCE_LOW:
        return (
            PRELIMINARY_SEVERITY_UNSCORED,
            "Insufficient confidence for preliminary severity annotation.",
        )

    return (
        PRELIMINARY_SEVERITY_UNSCORED,
        "No preliminary severity policy matched.",
    )


def dedupe_severity_annotations(
    annotations: list[SeverityAnnotatedConcern],
) -> list[SeverityAnnotatedConcern]:
    """Deduplicate severity annotations while preserving first-seen order."""
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    out: list[SeverityAnnotatedConcern] = []

    for annotation in annotations:
        if annotation.key in seen:
            continue
        seen.add(annotation.key)
        out.append(annotation)

    return out