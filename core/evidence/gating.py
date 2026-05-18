"""Evidence-gating helpers for curated ontology facts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from core.evidence.traces import build_pd_effect_traces_for_drug_effect
from core.models import Facts, PDEffect

EVIDENCE_MODE_OFF = "off"
EVIDENCE_MODE_SUPPORTED = "supported"
EVIDENCE_MODE_MODERATE = "moderate"
EVIDENCE_MODE_STRICT = "strict"

VALID_EVIDENCE_MODES = {
    EVIDENCE_MODE_OFF,
    EVIDENCE_MODE_SUPPORTED,
    EVIDENCE_MODE_MODERATE,
    EVIDENCE_MODE_STRICT,
}

_CONFIDENCE_RANK = {
    "low": 1,
    "uncertain": 2,
    "moderate": 3,
    "high": 4,
}


class EvidenceGatingModeError(ValueError):
    """Raised when an unsupported evidence gating mode is requested."""


def require_valid_evidence_mode(mode: str) -> None:
    """Raise if an evidence gating mode is unsupported."""
    if mode not in VALID_EVIDENCE_MODES:
        allowed = ", ".join(sorted(VALID_EVIDENCE_MODES))
        raise EvidenceGatingModeError(
            f"Unsupported evidence mode: {mode}. Expected one of: {allowed}"
        )


def _confidence_level_rank(level: str | None) -> int:
    if level is None:
        return 0

    return _CONFIDENCE_RANK.get(level, 0)


def _claim_supporting_count(claim_trace: dict[str, Any]) -> int:
    counts = claim_trace.get("evidence_support_counts")

    if not isinstance(counts, dict):
        return 0

    value = counts.get("supporting", 0)

    if not isinstance(value, int):
        return 0

    return value


def _claim_confidence_level(claim_trace: dict[str, Any]) -> str | None:
    confidence = claim_trace.get("evidence_confidence")

    if not isinstance(confidence, dict):
        return None

    level = confidence.get("level")

    if not isinstance(level, str):
        return None

    return level


def _claim_has_supporting_evidence(claim_trace: dict[str, Any]) -> bool:
    return _claim_supporting_count(claim_trace) > 0


def _claim_is_cleanly_supported(claim_trace: dict[str, Any]) -> bool:
    return claim_trace.get("evidence_support_status") == "supported"


def _claim_meets_minimum_confidence(
    claim_trace: dict[str, Any],
    minimum_level: str,
) -> bool:
    return _confidence_level_rank(
        _claim_confidence_level(claim_trace),
    ) >= _confidence_level_rank(minimum_level)


def claim_trace_satisfies_evidence_mode(
    claim_trace: dict[str, Any],
    mode: str,
) -> bool:
    """Return whether a claim trace satisfies an evidence mode."""
    require_valid_evidence_mode(mode)

    if mode == EVIDENCE_MODE_OFF:
        return True

    if mode == EVIDENCE_MODE_SUPPORTED:
        return _claim_has_supporting_evidence(claim_trace)

    if mode == EVIDENCE_MODE_MODERATE:
        return (
            _claim_has_supporting_evidence(claim_trace)
            and _claim_meets_minimum_confidence(claim_trace, "moderate")
        )

    if mode == EVIDENCE_MODE_STRICT:
        return (
            _claim_is_cleanly_supported(claim_trace)
            and _claim_meets_minimum_confidence(claim_trace, "high")
        )

    return False


def pd_effect_has_evidence_for_mode(
    drug_id: str,
    effect_id: str,
    *,
    mode: str = EVIDENCE_MODE_SUPPORTED,
) -> bool:
    """Return whether a drug/effect pair satisfies an evidence mode."""
    require_valid_evidence_mode(mode)

    if mode == EVIDENCE_MODE_OFF:
        return True

    claim_traces = build_pd_effect_traces_for_drug_effect(
        drug_id,
        effect_id,
    )

    return any(
        claim_trace_satisfies_evidence_mode(
            claim_trace,
            mode,
        )
        for claim_trace in claim_traces
    )


def is_pd_effect_evidence_backed(
    drug_id: str,
    effect: PDEffect,
    *,
    mode: str = EVIDENCE_MODE_SUPPORTED,
) -> bool:
    """Return whether a drug PD effect satisfies an evidence mode."""
    return pd_effect_has_evidence_for_mode(
        drug_id,
        effect.effect_id,
        mode=mode,
    )


def filter_pd_effects_to_evidence_backed(
    drug_id: str,
    effects: list[PDEffect],
    *,
    mode: str = EVIDENCE_MODE_SUPPORTED,
) -> list[PDEffect]:
    """Return only PD effects that satisfy an evidence mode."""
    require_valid_evidence_mode(mode)

    if mode == EVIDENCE_MODE_OFF:
        return list(effects)

    return [
        effect
        for effect in effects
        if is_pd_effect_evidence_backed(
            drug_id,
            effect,
            mode=mode,
        )
    ]


def filter_facts_to_evidence_backed_pd_effects(
    facts: Facts,
    *,
    mode: str = EVIDENCE_MODE_SUPPORTED,
) -> Facts:
    """Return a Facts copy with PD effects filtered by evidence mode.

    This only filters pharmacodynamic effects. Drug records, enzyme roles,
    and transporter roles are preserved unchanged.
    """
    require_valid_evidence_mode(mode)

    if mode == EVIDENCE_MODE_OFF:
        return deepcopy(facts)

    filtered_facts = deepcopy(facts)
    filtered_pd_effects = {}

    for drug_id, effects in facts.pd_effects.items():
        evidence_backed_effects = filter_pd_effects_to_evidence_backed(
            drug_id,
            effects,
            mode=mode,
        )

        if evidence_backed_effects:
            filtered_pd_effects[drug_id] = evidence_backed_effects

    filtered_facts.pd_effects = filtered_pd_effects

    return filtered_facts