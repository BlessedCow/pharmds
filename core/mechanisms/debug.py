"""Debug formatting helpers for MechanismEffect IR.

These helpers are intentionally read-only. They are meant for inspection during
development and should not affect rule scoring, severity, or recommendations.
"""

from __future__ import annotations

from typing import Any

from core.mechanisms.effects import MechanismEffect
from core.mechanisms.pairwise_adapter import PairwiseMechanismConcern
from core.mechanisms.registry import MECHANISM_PD_EFFECT

DEBUG_MECHANISM_PIPELINE_LABEL = "Mechanism Pipeline"
DEBUG_OLD_PAIRWISE_LABEL = "Old Pairwise Rule Pipeline"
DEBUG_PAIRWISE_MIGRATION_LABEL = "Pairwise Migration Debug"


def format_debug_section_title(source_label: str, detail_label: str) -> str:
    """Return a readable source-qualified debug section title."""
    return f"{source_label}: {detail_label}"


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


def format_pairwise_mechanism_concern(
    concern: PairwiseMechanismConcern,
) -> str:
    """Return a compact pairwise-shaped mechanism concern line."""
    pair = " + ".join(concern.pair_key)
    return (
        f"{pair} | domain={concern.domain}"
        f" | concern={concern.concern_id}"
        f" | object={concern.object_drug}"
        f" | source={concern.source_concern}"
        f" | severity={concern.severity}"
        f" | confidence={concern.confidence}"
    )


def format_pairwise_mechanism_concerns(
    concerns: list[PairwiseMechanismConcern] | tuple[PairwiseMechanismConcern, ...],
) -> list[str]:
    """Return compact pairwise-shaped mechanism concern lines."""
    return [format_pairwise_mechanism_concern(concern) for concern in concerns]


def format_old_pairwise_rule_report(report: Any) -> str:
    """Return a compact old pairwise rule report line for migration debug."""
    hits = [
        *(getattr(report, "pk_hits", None) or ()),
        *(getattr(report, "pd_hits", None) or ()),
    ]
    rule_ids = sorted(hit.rule_id for hit in hits)
    pair = " + ".join(sorted((report.drug_1, report.drug_2)))
    severity = getattr(getattr(report, "overall_severity", None), "value", "none")
    rule_class = getattr(getattr(report, "overall_rule_class", None), "value", "none")
    rules = ", ".join(rule_ids) if rule_ids else "none"
    return (
        f"{pair} | severity={severity}"
        f" | class={rule_class}"
        f" | rules={rules}"
    )


def format_old_pairwise_rule_reports(
    reports: list[Any] | tuple[Any, ...],
) -> list[str]:
    """Return compact old pairwise rule report lines for migration debug."""
    return [format_old_pairwise_rule_report(report) for report in reports]