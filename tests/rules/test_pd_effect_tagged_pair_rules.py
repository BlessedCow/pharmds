from __future__ import annotations

from pathlib import Path

from app.cli import RULE_DIR
from app.runtime.domains import filter_rules_for_selected_pd_effects
from rules.engine import load_rules, rule_mechanisms
from tests.rules.pd_support import pd_rule_ids

RULE_ID = "PD_BUPROPION_ALCOHOL"


def _load_bupropion_alcohol_rule():
    rules = load_rules(Path(RULE_DIR))
    return next(rule for rule in rules if rule.id == RULE_ID)


def test_explicit_pd_drug_pair_rule_is_tagged_as_pd() -> None:
    rule = _load_bupropion_alcohol_rule()

    assert rule_mechanisms(rule) == ["pd"]

def test_specific_seizure_risk_filter_keeps_bupropion_alcohol_rule() -> None:
    rule = _load_bupropion_alcohol_rule()

    filtered = filter_rules_for_selected_pd_effects(
        [rule],
        ["seizure_risk"],
    )

    assert [item.id for item in filtered] == [RULE_ID]

def test_unrelated_pd_effect_filter_removes_bupropion_alcohol_rule() -> None:
    rule = _load_bupropion_alcohol_rule()

    filtered = filter_rules_for_selected_pd_effects(
        [rule],
        ["photosensitivity_risk"],
    )

    assert filtered == []

def test_bupropion_alcohol_returns_contextual_pd_finding_for_all_effects() -> None:
    rule_ids = pd_rule_ids(("bupropion", "alcohol"), pd_effects=None)

    assert RULE_ID in rule_ids

def test_bupropion_alcohol_returns_contextual_pd_finding_for_seizure_risk() -> None:
    rule_ids = pd_rule_ids(("bupropion", "alcohol"), 
        pd_effects=["seizure_risk"],
    )

    assert RULE_ID in rule_ids

def test_bupropion_alcohol_does_not_return_rule_for_photosensitivity() -> None:
    rule_ids = pd_rule_ids(("bupropion", "alcohol"), 
        pd_effects=["photosensitivity_risk"],
    )

    assert RULE_ID not in rule_ids
