from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.evidence.pd_interaction_traces import (
    build_additive_pd_effect_evidence_trace,
)
from core.mechanisms.effects import MechanismEffect
from core.mechanisms.registry import (
    MECHANISM_ENZYME_INDUCTION,
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_SUBSTRATE,
    MECHANISM_PD_EFFECT,
    MECHANISM_TRANSPORTER_INDUCTION,
    MECHANISM_TRANSPORTER_INHIBITION,
    MECHANISM_TRANSPORTER_SUBSTRATE,
)

CANDIDATE_ENZYME_INHIBITION = "ENZYME_INHIBITION_EXPOSURE"
CANDIDATE_ENZYME_INDUCTION = "ENZYME_INDUCTION_EXPOSURE"
CANDIDATE_TRANSPORTER_INHIBITION = "TRANSPORTER_INHIBITION_EXPOSURE"
CANDIDATE_TRANSPORTER_INDUCTION = "TRANSPORTER_INDUCTION_EXPOSURE"
CANDIDATE_PD_SHARED_EFFECT = "PD_SHARED_EFFECT"


@dataclass(frozen=True)
class InteractionCandidate:
    """A possible interaction pattern inferred from MechanismEffect facts.

    This is not a final clinical rule hit.

    Attributes:
        candidate_type: Interaction pattern type.
        precipitant_drug: Drug causing the mechanism/effect.
        object_drug: Drug affected by the mechanism/effect.
        target: Enzyme/transporter target when applicable.
        effect_id: PD effect id when applicable.
        mechanism: Mechanism name from the precipitant effect.
        object_mechanism: Mechanism name from the object effect.
        explanation: Compact human-readable explanation.
    """

    candidate_type: str
    precipitant_drug: str
    object_drug: str
    target: str | None = None
    effect_id: str | None = None
    mechanism: str | None = None
    object_mechanism: str | None = None
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str, str | None, str | None]:
        """Stable dedupe key."""
        return (
            self.candidate_type,
            self.precipitant_drug,
            self.object_drug,
            self.target,
            self.effect_id,
        )


def find_interaction_candidates(
    effects: list[MechanismEffect],
) -> list[InteractionCandidate]:
    """Find possible interaction candidates from normalized IR facts."""
    candidates: list[InteractionCandidate] = []

    candidates.extend(_find_enzyme_candidates(effects))
    candidates.extend(_find_transporter_candidates(effects))
    candidates.extend(_find_shared_pd_effect_candidates(effects))

    return dedupe_interaction_candidates(candidates)


def _find_enzyme_candidates(
    effects: list[MechanismEffect],
) -> list[InteractionCandidate]:
    candidates: list[InteractionCandidate] = []

    substrates = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_ENZYME_SUBSTRATE
    ]
    inhibitors = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_ENZYME_INHIBITION
    ]
    inducers = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_ENZYME_INDUCTION
    ]

    for inhibitor in inhibitors:
        for substrate in substrates:
            if inhibitor.source_drug == substrate.source_drug:
                continue
            if inhibitor.target != substrate.target:
                continue

            candidates.append(
                InteractionCandidate(
                    candidate_type=CANDIDATE_ENZYME_INHIBITION,
                    precipitant_drug=inhibitor.source_drug,
                    object_drug=substrate.source_drug,
                    target=inhibitor.target,
                    mechanism=inhibitor.mechanism,
                    object_mechanism=substrate.mechanism,
                    explanation=(
                        f"{inhibitor.source_drug} inhibits {inhibitor.target}; "
                        f"{substrate.source_drug} is a {substrate.target} "
                        "substrate."
                    ),
                )
            )

    for inducer in inducers:
        for substrate in substrates:
            if inducer.source_drug == substrate.source_drug:
                continue
            if inducer.target != substrate.target:
                continue

            candidates.append(
                InteractionCandidate(
                    candidate_type=CANDIDATE_ENZYME_INDUCTION,
                    precipitant_drug=inducer.source_drug,
                    object_drug=substrate.source_drug,
                    target=inducer.target,
                    mechanism=inducer.mechanism,
                    object_mechanism=substrate.mechanism,
                    explanation=(
                        f"{inducer.source_drug} induces {inducer.target}; "
                        f"{substrate.source_drug} is a {substrate.target} "
                        "substrate."
                    ),
                )
            )

    return candidates


def _find_transporter_candidates(
    effects: list[MechanismEffect],
) -> list[InteractionCandidate]:
    candidates: list[InteractionCandidate] = []

    substrates = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_TRANSPORTER_SUBSTRATE
    ]
    inhibitors = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_TRANSPORTER_INHIBITION
    ]
    inducers = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_TRANSPORTER_INDUCTION
    ]

    for inhibitor in inhibitors:
        for substrate in substrates:
            if inhibitor.source_drug == substrate.source_drug:
                continue
            if inhibitor.target != substrate.target:
                continue

            candidates.append(
                InteractionCandidate(
                    candidate_type=CANDIDATE_TRANSPORTER_INHIBITION,
                    precipitant_drug=inhibitor.source_drug,
                    object_drug=substrate.source_drug,
                    target=inhibitor.target,
                    mechanism=inhibitor.mechanism,
                    object_mechanism=substrate.mechanism,
                    explanation=(
                        f"{inhibitor.source_drug} inhibits {inhibitor.target}; "
                        f"{substrate.source_drug} is a {substrate.target} "
                        "substrate."
                    ),
                )
            )

    for inducer in inducers:
        for substrate in substrates:
            if inducer.source_drug == substrate.source_drug:
                continue
            if inducer.target != substrate.target:
                continue

            candidates.append(
                InteractionCandidate(
                    candidate_type=CANDIDATE_TRANSPORTER_INDUCTION,
                    precipitant_drug=inducer.source_drug,
                    object_drug=substrate.source_drug,
                    target=inducer.target,
                    mechanism=inducer.mechanism,
                    object_mechanism=substrate.mechanism,
                    explanation=(
                        f"{inducer.source_drug} induces {inducer.target}; "
                        f"{substrate.source_drug} is a {substrate.target} "
                        "substrate."
                    ),
                )
            )

    return candidates


def _find_shared_pd_effect_candidates(
    effects: list[MechanismEffect],
) -> list[InteractionCandidate]:
    candidates: list[InteractionCandidate] = []

    pd_effects = [
        effect
        for effect in effects
        if effect.mechanism == MECHANISM_PD_EFFECT
    ]

    for left_index, left in enumerate(pd_effects):
        for right in pd_effects[left_index + 1:]:
            if left.source_drug == right.source_drug:
                continue
            if left.effect_id != right.effect_id:
                continue

            first, second = sorted([left.source_drug, right.source_drug])

            candidates.append(
                InteractionCandidate(
                    candidate_type=CANDIDATE_PD_SHARED_EFFECT,
                    precipitant_drug=first,
                    object_drug=second,
                    effect_id=left.effect_id,
                    mechanism=MECHANISM_PD_EFFECT,
                    object_mechanism=MECHANISM_PD_EFFECT,
                    explanation=(
                        f"{first} and {second} both contribute to "
                        f"{left.effect_id}."
                    ),
                    metadata={
                        "evidence_trace": build_additive_pd_effect_evidence_trace(
                            drug_ids=[first, second],
                            effect_id=left.effect_id,
                        )
                    },
                )
            )

    return candidates


def dedupe_interaction_candidates(
    candidates: list[InteractionCandidate],
) -> list[InteractionCandidate]:
    """Deduplicate candidates while preserving first-seen order."""
    seen: set[tuple[str, str, str, str | None, str | None]] = set()
    out: list[InteractionCandidate] = []

    for candidate in candidates:
        if candidate.key in seen:
            continue
        seen.add(candidate.key)
        out.append(candidate)

    return out
