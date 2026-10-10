from __future__ import annotations

import pytest

from tests.rules.pd_support import pd_rule_ids

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


@pytest.mark.parametrize(
    ("rule_id", "drugs", "effect_id"),
    TRIGGERABLE_CASES,
)
def test_new_pd_rules_run_with_all_effects(
    rule_id: str,
    drugs: tuple[str, str],
    effect_id: str,
) -> None:
    assert rule_id in pd_rule_ids(
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
    assert rule_id in pd_rule_ids(
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
    assert rule_id not in pd_rule_ids(
        drugs,
        pd_effects=["serotonergic"],
    )
