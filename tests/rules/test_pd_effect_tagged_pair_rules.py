from __future__ import annotations

from pathlib import Path

from app.cli import RULE_DIR
from app.runtime.domains import filter_rules_for_selected_pd_effects
from app.service import analyze_names
from rules.engine import load_rules, rule_mechanisms

RULE_ID = "PD_BUPROPION_ALCOHOL"


def _load_bupropion_alcohol_rule():
    rules = load_rules(Path(RULE_DIR))
    return next(rule for rule in rules if rule.id == RULE_ID)


def _pd_rule_ids(
    *,
    pd_effects: list[str] | None,
) -> set[str]:
    result = analyze_names(
        ["bupropion", "alcohol"],
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
    rule_ids = _pd_rule_ids(pd_effects=None)

    assert RULE_ID in rule_ids


def test_bupropion_alcohol_returns_contextual_pd_finding_for_seizure_risk() -> None:
    rule_ids = _pd_rule_ids(
        pd_effects=["seizure_risk"],
    )

    assert RULE_ID in rule_ids


def test_bupropion_alcohol_does_not_return_rule_for_photosensitivity() -> None:
    rule_ids = _pd_rule_ids(
        pd_effects=["photosensitivity_risk"],
    )

    assert RULE_ID not in rule_ids
