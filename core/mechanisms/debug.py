"""Debug formatting helpers for MechanismEffect IR.

These helpers are intentionally read-only. They are meant for inspection during
development and should not affect rule scoring, severity, or recommendations.
"""

from __future__ import annotations

from core.mechanisms.effects import MechanismEffect
from core.mechanisms.registry import MECHANISM_PD_EFFECT


def format_mechanism_effect(effect: MechanismEffect) -> str:
    """Return a compact human-readable representation of one IR fact."""
    if effect.mechanism == MECHANISM_PD_EFFECT:
        return (
            f"{effect.source_drug}: {effect.mechanism} "
            f"{effect.effect_id}"
        )

    return (
        f"{effect.source_drug}: {effect.mechanism} "
        f"{effect.target}"
    )


def format_mechanism_effects(
    effects: list[MechanismEffect],
) -> list[str]:
    """Return compact human-readable representations of IR facts."""
    return [format_mechanism_effect(effect) for effect in effects]
