import pytest

from core.evidence.gating import (
    EVIDENCE_MODE_MODERATE,
    EVIDENCE_MODE_OFF,
    EVIDENCE_MODE_STRICT,
    EVIDENCE_MODE_SUPPORTED,
    EvidenceGatingModeError,
    claim_trace_satisfies_evidence_mode,
    filter_facts_to_evidence_backed_pd_effects,
    pd_effect_has_evidence_for_mode,
    require_valid_evidence_mode,
)
from core.models import Facts, PDEffect


def _claim_trace(
    *,
    support_status="supported",
    supporting=1,
    disputing=0,
    confidence_level="moderate",
):
    return {
        "claim_id": "claim_test_drug_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "drug_id": "test_drug",
        "predicate": "has_pd_effect",
        "effect_id": "nausea",
        "claim_status": "active",
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": "2026-05-18",
        },
        "evidence_support_status": support_status,
        "evidence_support_counts": {
            "supporting": supporting,
            "disputing": disputing,
        },
        "evidence_confidence": {
            "level": confidence_level,
            "score": 60,
            "reasons": ["test reason"],
        },
        "evidence": [],
    }


def _effect(effect_id):
    return PDEffect(
        effect_id=effect_id,
        direction="increase",
        magnitude="medium",
    )


def test_require_valid_evidence_mode_accepts_known_modes():
    for mode in {
        EVIDENCE_MODE_OFF,
        EVIDENCE_MODE_SUPPORTED,
        EVIDENCE_MODE_MODERATE,
        EVIDENCE_MODE_STRICT,
    }:
        require_valid_evidence_mode(mode)


def test_require_valid_evidence_mode_rejects_unknown_mode():
    with pytest.raises(EvidenceGatingModeError):
        require_valid_evidence_mode("unknown")


def test_claim_trace_satisfies_off_mode():
    assert claim_trace_satisfies_evidence_mode(
        _claim_trace(
            support_status="disputed",
            supporting=0,
            disputing=1,
            confidence_level="low",
        ),
        EVIDENCE_MODE_OFF,
    )


def test_supported_mode_requires_supporting_evidence():
    assert claim_trace_satisfies_evidence_mode(
        _claim_trace(supporting=1),
        EVIDENCE_MODE_SUPPORTED,
    )

    assert not claim_trace_satisfies_evidence_mode(
        _claim_trace(
            support_status="disputed",
            supporting=0,
            disputing=1,
        ),
        EVIDENCE_MODE_SUPPORTED,
    )


def test_moderate_mode_requires_moderate_or_high_confidence():
    assert claim_trace_satisfies_evidence_mode(
        _claim_trace(confidence_level="moderate"),
        EVIDENCE_MODE_MODERATE,
    )
    assert claim_trace_satisfies_evidence_mode(
        _claim_trace(confidence_level="high"),
        EVIDENCE_MODE_MODERATE,
    )
    assert not claim_trace_satisfies_evidence_mode(
        _claim_trace(confidence_level="low"),
        EVIDENCE_MODE_MODERATE,
    )


def test_strict_mode_requires_clean_high_confidence_support():
    assert claim_trace_satisfies_evidence_mode(
        _claim_trace(
            support_status="supported",
            supporting=1,
            disputing=0,
            confidence_level="high",
        ),
        EVIDENCE_MODE_STRICT,
    )

    assert not claim_trace_satisfies_evidence_mode(
        _claim_trace(
            support_status="conflicting",
            supporting=1,
            disputing=1,
            confidence_level="high",
        ),
        EVIDENCE_MODE_STRICT,
    )

    assert not claim_trace_satisfies_evidence_mode(
        _claim_trace(
            support_status="supported",
            supporting=1,
            disputing=0,
            confidence_level="moderate",
        ),
        EVIDENCE_MODE_STRICT,
    )


def test_pd_effect_has_evidence_for_mode_uses_claim_traces(monkeypatch):
    monkeypatch.setattr(
        "core.evidence.gating.build_pd_effect_traces_for_drug_effect",
        lambda drug_id, effect_id: [
            _claim_trace(confidence_level="moderate"),
        ],
    )

    assert pd_effect_has_evidence_for_mode(
        "test_drug",
        "nausea",
        mode=EVIDENCE_MODE_SUPPORTED,
    )
    assert pd_effect_has_evidence_for_mode(
        "test_drug",
        "nausea",
        mode=EVIDENCE_MODE_MODERATE,
    )
    assert not pd_effect_has_evidence_for_mode(
        "test_drug",
        "nausea",
        mode=EVIDENCE_MODE_STRICT,
    )


def test_filter_facts_to_evidence_backed_pd_effects_uses_mode(monkeypatch):
    facts = Facts(
        pd_effects={
            "test_drug": [
                _effect("nausea"),
                _effect("sedation"),
            ],
        },
    )

    def fake_traces(drug_id, effect_id):
        if effect_id == "nausea":
            return [_claim_trace(confidence_level="moderate")]

        return [_claim_trace(confidence_level="low")]

    monkeypatch.setattr(
        "core.evidence.gating.build_pd_effect_traces_for_drug_effect",
        fake_traces,
    )

    filtered = filter_facts_to_evidence_backed_pd_effects(
        facts,
        mode=EVIDENCE_MODE_MODERATE,
    )

    assert list(filtered.pd_effects) == ["test_drug"]
    assert [
        effect.effect_id
        for effect in filtered.pd_effects["test_drug"]
    ] == ["nausea"]


def test_filter_facts_off_mode_preserves_pd_effects(monkeypatch):
    facts = Facts(
        pd_effects={
            "test_drug": [
                _effect("nausea"),
                _effect("sedation"),
            ],
        },
    )

    filtered = filter_facts_to_evidence_backed_pd_effects(
        facts,
        mode=EVIDENCE_MODE_OFF,
    )

    assert [
        effect.effect_id
        for effect in filtered.pd_effects["test_drug"]
    ] == [
        "nausea",
        "sedation",
    ]
    assert filtered is not facts