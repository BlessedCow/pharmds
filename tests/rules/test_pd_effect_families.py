from __future__ import annotations

import pytest

from app.service import analyze_names
from core.pd_effect_families import (
    PD_EFFECT_RULE_FAMILIES,
    canonical_pd_effect_family,
    pd_effects_share_family,
)

EXPECTED_FAMILIES = {
    "blood_pressure_increase": "hypertension",
    "hypertension_risk": "hypertension",
    "lithium_increase_risk": "lithium_level_increase_risk",
    "seizure_threshold": "seizure_risk",
    "sympathomimetic_activity": "sympathetic_stimulation",
    "tachycardia_risk": "tachycardia",
}


@pytest.mark.parametrize(
    ("source_effect", "rule_effect"),
    tuple(EXPECTED_FAMILIES.items()),
)
def test_pd_effect_family_mapping_is_executable(
    source_effect: str,
    rule_effect: str,
) -> None:
    assert canonical_pd_effect_family(source_effect) == rule_effect
    assert pd_effects_share_family(source_effect, rule_effect)
    assert pd_effects_share_family(rule_effect, source_effect)


def test_pd_effect_family_inventory_is_stable() -> None:
    assert PD_EFFECT_RULE_FAMILIES == EXPECTED_FAMILIES


@pytest.mark.parametrize(
    ("drugs", "selected_effect", "expected_rule_id"),
    (
        (
            ("bupropion", "amitriptyline"),
            "seizure_threshold",
            "PD_SEIZURE_RISK_ADDITIVE",
        ),
        (
            ("methylphenidate", "amphetamine_dextroamphetamine"),
            "sympathomimetic_activity",
            "PD_SYMPATHETIC_STIMULATION_ADDITIVE",
        ),
        (
            ("ibuprofen", "lisinopril"),
            "lithium_increase_risk",
            "PD_LITHIUM_LEVEL_INCREASE_RISK",
        ),
    ),
)
def test_mapped_pd_effects_trigger_existing_rule_families(
    drugs: tuple[str, str],
    selected_effect: str,
    expected_rule_id: str,
) -> None:
    result = analyze_names(
        list(drugs),
        domain="all",
        pd_effects=[selected_effect],
        as_json_payload=True,
    )

    assert result.ok

    rule_ids = {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair["pd"]["hits"]
    }

    assert expected_rule_id in rule_ids


def test_seizure_risk_selector_keeps_seizure_threshold_facts() -> None:
    result = analyze_names(
        ["bupropion", "amitriptyline"],
        domain="all",
        pd_effects=["seizure_risk"],
        as_json_payload=True,
    )

    assert result.ok

    rule_ids = {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair["pd"]["hits"]
    }

    assert "PD_SEIZURE_RISK_ADDITIVE" in rule_ids
