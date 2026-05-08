from __future__ import annotations

from dataclasses import dataclass

from core.mechanism_policy import (
    POLICY_EXPOSURE_REDUCTION_CONCERN,
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)

AGGREGATE_OBJECT_EXPOSURE_INCREASE = "object_exposure_increase_cluster"
AGGREGATE_OBJECT_EXPOSURE_DECREASE = "object_exposure_decrease_cluster"
AGGREGATE_SHARED_PD_EFFECT = "shared_pd_effect_cluster"
AGGREGATE_SAFETY_CONCERN = "safety_concern_cluster"
AGGREGATE_TOLERABILITY_CONCERN = "tolerability_concern_cluster"


@dataclass(frozen=True)
class AggregateConcern:
    """Grouped concern across one or more policy results.

    Attributes:
        aggregate_type: Type of grouped concern.
        anchor: Main grouping value, such as object drug or PD effect id.
        policy_concern: Source policy concern category.
        drugs: Drugs involved in the grouped concern.
        targets: Enzyme/transporter targets involved, when applicable.
        effect_id: Shared PD effect id, when applicable.
        members: Original policy result members.
        explanation: Compact explanation of the grouped concern.
    """

    aggregate_type: str
    anchor: str
    policy_concern: str
    drugs: tuple[str, ...]
    targets: tuple[str, ...] = ()
    effect_id: str | None = None
    members: tuple[ConcernPolicyResult, ...] = ()
    explanation: str = ""

    @property
    def key(self) -> tuple[str, str, str | None]:
        """Stable dedupe key."""
        return (self.aggregate_type, self.anchor, self.effect_id)


def aggregate_policy_results(
    results: list[ConcernPolicyResult],
) -> list[AggregateConcern]:
    """Group policy concern results into aggregate concerns."""
    aggregates: list[AggregateConcern] = []

    aggregates.extend(_aggregate_object_exposure_increases(results))
    aggregates.extend(_aggregate_object_exposure_decreases(results))
    aggregates.extend(_aggregate_shared_pd_effects(results))
    aggregates.extend(_aggregate_safety_concerns(results))
    aggregates.extend(_aggregate_tolerability_concerns(results))

    return dedupe_aggregate_concerns(aggregates)


def _aggregate_object_exposure_increases(
    results: list[ConcernPolicyResult],
) -> list[AggregateConcern]:
    grouped: dict[str, list[ConcernPolicyResult]] = {}

    for result in results:
        if result.policy_concern != POLICY_MECHANISTIC_CONCERN:
            continue
        if not result.target:
            continue
        grouped.setdefault(result.object_drug, []).append(result)

    aggregates: list[AggregateConcern] = []

    for object_drug, members in grouped.items():
        drugs = _unique_sorted(
            drug
            for member in members
            for drug in (member.precipitant_drug, member.object_drug)
        )
        targets = _unique_sorted(
            member.target
            for member in members
            if member.target
        )

        aggregates.append(
            AggregateConcern(
                aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
                anchor=object_drug,
                policy_concern=POLICY_MECHANISTIC_CONCERN,
                drugs=drugs,
                targets=targets,
                members=tuple(members),
                explanation=(
                    f"{object_drug} has {len(members)} exposure-increase "
                    "candidate(s)."
                ),
            )
        )

    return aggregates


def _aggregate_object_exposure_decreases(
    results: list[ConcernPolicyResult],
) -> list[AggregateConcern]:
    grouped: dict[str, list[ConcernPolicyResult]] = {}

    for result in results:
        if result.policy_concern != POLICY_EXPOSURE_REDUCTION_CONCERN:
            continue
        if not result.target:
            continue
        grouped.setdefault(result.object_drug, []).append(result)

    aggregates: list[AggregateConcern] = []

    for object_drug, members in grouped.items():
        drugs = _unique_sorted(
            drug
            for member in members
            for drug in (member.precipitant_drug, member.object_drug)
        )
        targets = _unique_sorted(
            member.target
            for member in members
            if member.target
        )

        aggregates.append(
            AggregateConcern(
                aggregate_type=AGGREGATE_OBJECT_EXPOSURE_DECREASE,
                anchor=object_drug,
                policy_concern=POLICY_EXPOSURE_REDUCTION_CONCERN,
                drugs=drugs,
                targets=targets,
                members=tuple(members),
                explanation=(
                    f"{object_drug} has {len(members)} exposure-decrease "
                    "candidate(s)."
                ),
            )
        )

    return aggregates


def _aggregate_shared_pd_effects(
    results: list[ConcernPolicyResult],
) -> list[AggregateConcern]:
    grouped: dict[str, list[ConcernPolicyResult]] = {}

    for result in results:
        if not result.effect_id:
            continue
        grouped.setdefault(result.effect_id, []).append(result)

    aggregates: list[AggregateConcern] = []

    for effect_id, members in grouped.items():
        drugs = _unique_sorted(
            drug
            for member in members
            for drug in (member.precipitant_drug, member.object_drug)
        )

        aggregates.append(
            AggregateConcern(
                aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
                anchor=effect_id,
                policy_concern=members[0].policy_concern,
                drugs=drugs,
                effect_id=effect_id,
                members=tuple(members),
                explanation=(
                    f"{len(drugs)} selected drug(s) are linked to "
                    f"{effect_id}."
                ),
            )
        )

    return aggregates


def _aggregate_safety_concerns(
    results: list[ConcernPolicyResult],
) -> list[AggregateConcern]:
    return _aggregate_by_policy_concern(
        results,
        policy_concern=POLICY_SAFETY_CONCERN,
        aggregate_type=AGGREGATE_SAFETY_CONCERN,
    )


def _aggregate_tolerability_concerns(
    results: list[ConcernPolicyResult],
) -> list[AggregateConcern]:
    return _aggregate_by_policy_concern(
        results,
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        aggregate_type=AGGREGATE_TOLERABILITY_CONCERN,
    )


def _aggregate_by_policy_concern(
    results: list[ConcernPolicyResult],
    *,
    policy_concern: str,
    aggregate_type: str,
) -> list[AggregateConcern]:
    members = [
        result
        for result in results
        if result.policy_concern == policy_concern
    ]

    if not members:
        return []

    drugs = _unique_sorted(
        drug
        for member in members
        for drug in (member.precipitant_drug, member.object_drug)
    )
    effects = _unique_sorted(
        member.effect_id
        for member in members
        if member.effect_id
    )

    return [
        AggregateConcern(
            aggregate_type=aggregate_type,
            anchor=policy_concern,
            policy_concern=policy_concern,
            drugs=drugs,
            effect_id=", ".join(effects) if effects else None,
            members=tuple(members),
            explanation=(
                f"{len(members)} {policy_concern} policy result(s) "
                "were identified."
            ),
        )
    ]


def dedupe_aggregate_concerns(
    concerns: list[AggregateConcern],
) -> list[AggregateConcern]:
    """Deduplicate aggregate concerns while preserving first-seen order."""
    seen: set[tuple[str, str, str | None]] = set()
    out: list[AggregateConcern] = []

    for concern in concerns:
        if concern.key in seen:
            continue
        seen.add(concern.key)
        out.append(concern)

    return out


def _unique_sorted(values) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value}))