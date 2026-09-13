from __future__ import annotations

import pytest

from app.service import analyze_names

TRIGGERABLE_CASES = (
    (
        "PD_ANTICHOLINERGIC_EFFECTS_ADDITIVE",
        ("hydroxyzine", "amitriptyline"),
        "anticholinergic_effects",
    ),
    (
        "PD_HYPOKALEMIA_RISK_ADDITIVE",
        ("hydrochlorothiazide", "aloe_vera"),
        "hypokalemia_risk",
    ),
    (
        "PD_NEUROTOXICITY_RISK_ADDITIVE",
        ("lithium", "topiramate"),
        "neurotoxicity_risk",
    ),
    (
        "PD_NORADRENERGIC_EFFECTS_ADDITIVE",
        ("venlafaxine", "bupropion"),
        "noradrenergic_effects",
    ),
    (
        "PD_URINARY_RETENTION_RISK_ADDITIVE",
        ("vibegron", "mecamylamine"),
        "urinary_retention_risk",
    ),
)


def _pd_rule_ids(
    drugs: tuple[str, str],
    *,
    pd_effects: list[str] | None,
) -> set[str]:
    result = analyze_names(
        list(drugs),
        domain="all",
        pd_effects=pd_effects,
        as_json_payload=True,
    )

    assert result.ok

    return {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair["pd"]["hits"]
    }


@pytest.mark.parametrize(
    ("rule_id", "drugs", "effect_id"),
    TRIGGERABLE_CASES,
)
def test_new_pd_rules_run_with_all_effects(
    rule_id: str,
    drugs: tuple[str, str],
    effect_id: str,
) -> None:
    assert rule_id in _pd_rule_ids(
        drugs,
        pd_effects=None,
    )


@pytest.mark.parametrize(
    ("rule_id", "drugs", "effect_id"),
    TRIGGERABLE_CASES,
)
def test_new_pd_rules_run_with_specific_effect_filter(
    rule_id: str,
    drugs: tuple[str, str],
    effect_id: str,
) -> None:
    assert rule_id in _pd_rule_ids(
        drugs,
        pd_effects=[effect_id],
    )


@pytest.mark.parametrize(
    ("rule_id", "drugs", "effect_id"),
    TRIGGERABLE_CASES,
)
def test_new_pd_rules_are_removed_by_unrelated_filter(
    rule_id: str,
    drugs: tuple[str, str],
    effect_id: str,
) -> None:
    assert rule_id not in _pd_rule_ids(
        drugs,
        pd_effects=["serotonergic"],
    )
