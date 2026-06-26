from __future__ import annotations

import pytest

from app.cli import RULE_DIR, _parse_domain_selection, filter_rules_for_selected_domains
from app.service import analyze_names
from rules.engine import load_rules, rule_mechanisms

NAMED_PAIR_RULE_CASES = [
    pytest.param(
        ["doxycycline", "amoxicillin"],
        "PK_DOXYCYCLINE_AMOXICILLIN",
        id="doxycycline-amoxicillin",
    ),
    pytest.param(
        ["doxycycline", "calcium carbonate"],
        "PK_DOXYCYCLINE_CALCIUM_CARBONATE",
        id="doxycycline-calcium-carbonate",
    ),
    pytest.param(
        ["doxycycline", "warfarin"],
        "PK_DOXYCYCLINE_WARFARIN",
        id="doxycycline-warfarin",
    ),
    pytest.param(
        ["lisdexamfetamine", "fluoxetine"],
        "PK_LISDEXAMFETAMINE_FLUOXETINE",
        id="lisdexamfetamine-fluoxetine",
    ),
    pytest.param(
        ["methadone", "carbamazepine"],
        "PK_METHADONE_CARBAMAZEPINE",
        id="methadone-carbamazepine",
    ),
    pytest.param(
        ["methadone", "fluoxetine"],
        "PK_METHADONE_FLUOXETINE",
        id="methadone-fluoxetine",
    ),
    pytest.param(
        ["vibegron", "digoxin"],
        "PK_VIBEGRON_DIGOXIN",
        id="vibegron-digoxin",
    ),
]


def _pk_rule_ids_for(drug_names: list[str], *, domain: str = "all") -> set[str]:
    result = analyze_names(drug_names, domain=domain, as_json_payload=True)

    assert result.ok

    return {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair["pk"]["hits"]
    }


@pytest.mark.parametrize(("drug_names", "rule_id"), NAMED_PAIR_RULE_CASES)
def test_named_pair_pk_rules_are_included_in_default_and_pk_domains(
    drug_names: list[str],
    rule_id: str,
) -> None:
    assert rule_id in _pk_rule_ids_for(drug_names)
    assert rule_id in _pk_rule_ids_for(drug_names, domain="pk")


@pytest.mark.parametrize(("drug_names", "rule_id"), NAMED_PAIR_RULE_CASES)
def test_named_pair_pk_rules_remain_excluded_from_pd_domain(
    drug_names: list[str],
    rule_id: str,
) -> None:
    assert rule_id not in _pk_rule_ids_for(drug_names, domain="pd")


def test_named_pair_rules_have_filterable_mechanism_tag() -> None:
    rules = load_rules(RULE_DIR)
    named_pair_rules = [
        rule
        for rule in rules
        if rule.domain == "PK" and "drug_pair" in rule.logic
    ]

    assert named_pair_rules
    assert "named_pair" in _parse_domain_selection("all")
    assert "named_pair" in _parse_domain_selection("pk")

    selected_rules = filter_rules_for_selected_domains(
        rules,
        _parse_domain_selection("all"),
    )

    for rule in named_pair_rules:
        assert rule_mechanisms(rule) == ["named_pair"]
        assert rule in selected_rules