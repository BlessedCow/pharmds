"""Evidence-gating helpers for curated ontology facts."""

from __future__ import annotations

from copy import deepcopy

from core.evidence.traces import has_approved_active_pd_effect_evidence
from core.models import Facts, PDEffect


def is_pd_effect_evidence_backed(
    drug_id: str,
    effect: PDEffect,
) -> bool:
    """Return whether a drug PD effect has approved active evidence."""
    return has_approved_active_pd_effect_evidence(
        drug_id,
        effect.effect_id,
    )


def filter_pd_effects_to_evidence_backed(
    drug_id: str,
    effects: list[PDEffect],
) -> list[PDEffect]:
    """Return only PD effects with approved active evidence claims."""
    return [
        effect
        for effect in effects
        if is_pd_effect_evidence_backed(drug_id, effect)
    ]


def filter_facts_to_evidence_backed_pd_effects(facts: Facts) -> Facts:
    """Return a Facts copy with PD effects filtered to evidence-backed facts.

    This only filters pharmacodynamic effects. Drug records, enzyme roles,
    and transporter roles are preserved unchanged.
    """
    filtered_facts = deepcopy(facts)

    filtered_pd_effects = {}

    for drug_id, effects in facts.pd_effects.items():
        evidence_backed_effects = filter_pd_effects_to_evidence_backed(
            drug_id,
            effects,
        )

        if evidence_backed_effects:
            filtered_pd_effects[drug_id] = evidence_backed_effects

    filtered_facts.pd_effects = filtered_pd_effects

    return filtered_facts