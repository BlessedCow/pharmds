"""Inference helpers for selected-drug MechanismEffect IR."""

from __future__ import annotations

from core.mechanisms.effects import (
    MechanismEffect,
    dedupe_mechanism_effects,
    facts_to_mechanism_effects,
)
from core.models import Facts


def infer_mechanism_effects_for_drugs(
    drug_ids: list[str],
    facts: Facts,
) -> list[MechanismEffect]:
    """Return normalized mechanism/effect facts for selected drugs only."""
    selected = set(drug_ids)
    all_effects = facts_to_mechanism_effects(facts)

    return dedupe_mechanism_effects(
        [
            effect
            for effect in all_effects
            if effect.source_drug in selected
        ]
    )
