"""Normalized pharmacology mechanism/effect intermediate representation.

This module adds a semantic IR layer without changing current rule output.
A MechanismEffect is a pharmacology fact, not a final recommendation.
Severity and action policy should be derived later by arbitration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.constants import normalize_pd_effect_id, normalize_transporter_id
from core.mechanism_registry import (
    ENZYME_ROLE_TO_MECHANISM,
    MECHANISM_PD_EFFECT,
    TRANSPORTER_ROLE_TO_MECHANISM,
    validate_mechanism,
    validate_pd_effect,
)
from core.models import EnzymeRole, Facts, PDEffect, TransporterRole


@dataclass(frozen=True)
class MechanismEffect:
    """A normalized pharmacology fact.

    Examples:
        - bupropion inhibits CYP2D6
        - rifampin induces CYP3A4
        - digoxin is a P-gp substrate
        - vortioxetine increases nausea risk

    This object intentionally does not contain final clinical severity.
    """

    mechanism: str
    source_drug: str
    target: str | None = None
    effect_id: str | None = None
    role: str | None = None
    strength: str | None = None
    direction: str | None = None
    magnitude: str | None = None
    fraction_metabolized: float | None = None
    mechanism_note: str | None = None
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_mechanism(self.mechanism)

        if self.mechanism == MECHANISM_PD_EFFECT:
            if not self.effect_id:
                raise ValueError("PD_EFFECT requires effect_id")
            object.__setattr__(self, "effect_id", validate_pd_effect(self.effect_id))
            return

        if not self.target:
            raise ValueError(f"{self.mechanism} requires target")

    @property
    def key(self) -> tuple[str, str, str | None, str | None]:
        """Stable dedupe key preserving drug-specific facts."""
        return (self.source_drug, self.mechanism, self.target, self.effect_id)


def enzyme_role_to_mechanism_effect(
    drug_id: str,
    role: EnzymeRole,
) -> MechanismEffect:
    """Convert an existing EnzymeRole into a normalized IR fact."""
    try:
        mechanism = ENZYME_ROLE_TO_MECHANISM[role.role]
    except KeyError as exc:
        raise ValueError(f"Unknown enzyme role: {role.role}") from exc

    return MechanismEffect(
        mechanism=mechanism,
        source_drug=drug_id,
        target=role.enzyme_id,
        role=role.role,
        strength=role.strength,
        fraction_metabolized=role.fraction_metabolized,
        mechanism_note=role.notes,
    )


def transporter_role_to_mechanism_effect(
    drug_id: str,
    role: TransporterRole,
) -> MechanismEffect:
    """Convert an existing TransporterRole into a normalized IR fact."""
    try:
        mechanism = TRANSPORTER_ROLE_TO_MECHANISM[role.role]
    except KeyError as exc:
        raise ValueError(f"Unknown transporter role: {role.role}") from exc

    return MechanismEffect(
        mechanism=mechanism,
        source_drug=drug_id,
        target=normalize_transporter_id(role.transporter_id),
        role=role.role,
        strength=role.strength,
        mechanism_note=role.notes,
    )


def pd_effect_to_mechanism_effect(
    drug_id: str,
    effect: PDEffect,
) -> MechanismEffect:
    """Convert an existing PDEffect into a normalized IR fact."""
    return MechanismEffect(
        mechanism=MECHANISM_PD_EFFECT,
        source_drug=drug_id,
        effect_id=normalize_pd_effect_id(effect.effect_id),
        direction=effect.direction,
        magnitude=effect.magnitude,
        mechanism_note=effect.mechanism_note,
    )


def facts_to_mechanism_effects(facts: Facts) -> list[MechanismEffect]:
    """Convert loaded Facts into normalized MechanismEffect objects."""
    effects: list[MechanismEffect] = []

    for drug_id in sorted(facts.drugs):
        for role in facts.enzyme_roles.get(drug_id, []) or []:
            effects.append(enzyme_role_to_mechanism_effect(drug_id, role))

        for role in facts.transporter_roles.get(drug_id, []) or []:
            effects.append(transporter_role_to_mechanism_effect(drug_id, role))

        for effect in facts.pd_effects.get(drug_id, []) or []:
            effects.append(pd_effect_to_mechanism_effect(drug_id, effect))

    return dedupe_mechanism_effects(effects)


def drug_to_mechanism_effects(
    drug_id: str,
    drug_data: dict[str, Any],
) -> list[MechanismEffect]:
    """Convert one curation drug dictionary into normalized IR facts.

    This supports the current data/curation/drugs.json shape:
        enzymes: [{enzyme_id, role, strength, fraction_metabolized, notes}]
        transporters: [{transporter_id, role, strength, notes}]
        pd_effects: [{effect_id, direction, magnitude, mechanism_note}]
    """
    effects: list[MechanismEffect] = []

    for role in drug_data.get("enzymes", []) or []:
        effects.append(
            enzyme_role_to_mechanism_effect(
                drug_id,
                EnzymeRole(
                    enzyme_id=role["enzyme_id"],
                    role=role["role"],
                    strength=role.get("strength"),
                    fraction_metabolized=role.get("fraction_metabolized"),
                    notes=role.get("notes"),
                ),
            )
        )

    for role in drug_data.get("transporters", []) or []:
        effects.append(
            transporter_role_to_mechanism_effect(
                drug_id,
                TransporterRole(
                    transporter_id=role["transporter_id"],
                    role=role["role"],
                    strength=role.get("strength"),
                    notes=role.get("notes"),
                ),
            )
        )

    for effect in drug_data.get("pd_effects", []) or []:
        effects.append(
            pd_effect_to_mechanism_effect(
                drug_id,
                PDEffect(
                    effect_id=effect["effect_id"],
                    direction=effect["direction"],
                    magnitude=effect["magnitude"],
                    mechanism_note=effect.get("mechanism_note"),
                ),
            )
        )

    return dedupe_mechanism_effects(effects)


def dedupe_mechanism_effects(
    effects: list[MechanismEffect],
) -> list[MechanismEffect]:
    """Deduplicate MechanismEffects while preserving first-seen order."""
    seen: set[tuple[str, str, str | None, str | None]] = set()
    out: list[MechanismEffect] = []

    for effect in effects:
        if effect.key in seen:
            continue
        seen.add(effect.key)
        out.append(effect)

    return out