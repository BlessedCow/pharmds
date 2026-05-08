"""Canonical mechanism/effect names for the normalized IR layer."""

from __future__ import annotations

import core.constants as c
from core.constants import normalize_pd_effect_id

MECHANISM_ENZYME_SUBSTRATE = "ENZYME_SUBSTRATE"
MECHANISM_ENZYME_INHIBITION = "ENZYME_INHIBITION"
MECHANISM_ENZYME_INDUCTION = "ENZYME_INDUCTION"
MECHANISM_TRANSPORTER_SUBSTRATE = "TRANSPORTER_SUBSTRATE"
MECHANISM_TRANSPORTER_INHIBITION = "TRANSPORTER_INHIBITION"
MECHANISM_TRANSPORTER_INDUCTION = "TRANSPORTER_INDUCTION"
MECHANISM_PD_EFFECT = "PD_EFFECT"

VALID_MECHANISMS = {
    MECHANISM_ENZYME_SUBSTRATE,
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_INDUCTION,
    MECHANISM_TRANSPORTER_SUBSTRATE,
    MECHANISM_TRANSPORTER_INHIBITION,
    MECHANISM_TRANSPORTER_INDUCTION,
    MECHANISM_PD_EFFECT,
}

ENZYME_ROLE_TO_MECHANISM = {
    "substrate": MECHANISM_ENZYME_SUBSTRATE,
    "inhibitor": MECHANISM_ENZYME_INHIBITION,
    "inducer": MECHANISM_ENZYME_INDUCTION,
}

TRANSPORTER_ROLE_TO_MECHANISM = {
    "substrate": MECHANISM_TRANSPORTER_SUBSTRATE,
    "inhibitor": MECHANISM_TRANSPORTER_INHIBITION,
    "inducer": MECHANISM_TRANSPORTER_INDUCTION,
}

# Start from the canonical constants already used by the project.
VALID_PD_EFFECTS = {
    value
    for name, value in vars(c).items()
    if name.startswith("PD_EFFECT_") and isinstance(value, str)
}

# These currently appear in data/curation/drugs.json and are loaded by the app.
# Keeping them here prevents the new IR layer from rejecting existing project data.
VALID_PD_EFFECTS |= {
    "CNS_stimulation",
    "sympathetic_stimulation",
    "hypertension",
    "tachycardia",
}


def validate_mechanism(mechanism: str) -> str:
    """Validate and return a canonical mechanism name."""
    if mechanism not in VALID_MECHANISMS:
        raise ValueError(f"Unknown mechanism: {mechanism}")
    return mechanism


def validate_pd_effect(effect_id: str) -> str:
    """Normalize, validate, and return a canonical PD effect id."""
    normalized = normalize_pd_effect_id(effect_id)
    if normalized not in VALID_PD_EFFECTS:
        raise ValueError(f"Unknown PD effect: {effect_id}")
    return normalized
