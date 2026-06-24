from __future__ import annotations

from app.cli import RULE_DIR, _parse_domain_selection, filter_rules_for_selected_domains
from app.service import analyze_names
from rules.engine import load_rules, rule_mechanisms


def _pk_rule_ids_for(drug_names: list[str], *, domain: str = "all") -> set[str]:
    result = analyze_names(drug_names, domain=domain, as_json_payload=True)

    assert result.ok

    return {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair["pk"]["hits"]
    }


def test_named_pair_pk_rules_are_included_in_default_and_pk_domains() -> None:
    drug_names = ["doxycycline", "calcium carbonate"]

    assert "PK_DOXYCYCLINE_CALCIUM_CARBONATE" in _pk_rule_ids_for(drug_names)
    assert "PK_DOXYCYCLINE_CALCIUM_CARBONATE" in _pk_rule_ids_for(
        drug_names,
        domain="pk",
    )


def test_named_pair_pk_rules_remain_excluded_from_pd_domain() -> None:
    assert _pk_rule_ids_for(
        ["doxycycline", "calcium carbonate"],
        domain="pd",
    ) == set()


def test_named_pair_rules_have_filterable_mechanism_tag() -> None:
    rules = load_rules(RULE_DIR)
    doxycycline_calcium_rule = next(
        rule for rule in rules if rule.id == "PK_DOXYCYCLINE_CALCIUM_CARBONATE"
    )

    assert rule_mechanisms(doxycycline_calcium_rule) == ["named_pair"]
    assert "named_pair" in _parse_domain_selection("all")
    assert "named_pair" in _parse_domain_selection("pk")

    selected_rules = filter_rules_for_selected_domains(
        rules,
        _parse_domain_selection("all"),
    )

    assert doxycycline_calcium_rule in selected_rules