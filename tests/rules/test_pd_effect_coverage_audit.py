from __future__ import annotations

from tools.pd_effect_coverage_audit import (
    DOCUMENTED_PD_EFFECT_GAPS,
    PD_EFFECT_RULE_FAMILIES,
    build_pd_coverage_audit,
)

EXPECTED_CURATED_PD_EFFECT_COUNT = 43

EXPECTED_MAPPED_EFFECTS = {
    "blood_pressure_increase": "hypertension",
    "hypertension_risk": "hypertension",
    "lithium_increase_risk": "lithium_level_increase_risk",
    "seizure_threshold": "seizure_risk",
    "sympathomimetic_activity": "sympathetic_stimulation",
    "tachycardia_risk": "tachycardia",
}

EXPECTED_DOCUMENTED_GAPS = {
    "cholinergic_modulation",
    "hypersensitivity_risk",
    "nAChR_antagonism",
    "renal_function",
}


def test_pd_effect_coverage_audit_has_no_undocumented_effects() -> None:
    audit = build_pd_coverage_audit()

    assert audit.undocumented_effects == frozenset()


def test_pd_effect_coverage_audit_tracks_current_curated_inventory() -> None:
    audit = build_pd_coverage_audit()

    assert len(audit.curated_effects) == EXPECTED_CURATED_PD_EFFECT_COUNT


def test_pd_effect_family_mappings_are_documented_and_rule_backed() -> None:
    audit = build_pd_coverage_audit()

    assert PD_EFFECT_RULE_FAMILIES == EXPECTED_MAPPED_EFFECTS
    assert audit.mapped_effects == EXPECTED_MAPPED_EFFECTS

    for target_effect in EXPECTED_MAPPED_EFFECTS.values():
        assert (
            target_effect in audit.direct_rule_effects
            or target_effect in audit.explicit_pair_effects
        )


def test_pd_effect_coverage_gaps_are_explicitly_documented() -> None:
    audit = build_pd_coverage_audit()

    assert set(DOCUMENTED_PD_EFFECT_GAPS) == EXPECTED_DOCUMENTED_GAPS
    assert set(audit.documented_gaps) == EXPECTED_DOCUMENTED_GAPS
    assert audit.uncovered_curated_effects == EXPECTED_DOCUMENTED_GAPS


def test_bupropion_alcohol_effect_is_covered_by_explicit_pair_rule() -> None:
    audit = build_pd_coverage_audit()

    assert "seizure_risk" in audit.explicit_pair_effects


def test_seizure_threshold_maps_to_seizure_risk() -> None:
    audit = build_pd_coverage_audit()

    assert audit.mapped_effects["seizure_threshold"] == "seizure_risk"
