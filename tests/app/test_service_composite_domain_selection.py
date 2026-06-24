from __future__ import annotations

from app.service import analyze_names


def _pair_rule_ids(drug_names: list[str], *, domain: str) -> tuple[set[str], set[str]]:
    result = analyze_names(drug_names, domain=domain, as_json_payload=True)

    assert result.ok
    assert len(result.payload["pairs"]) == 1

    pair = result.payload["pairs"][0]
    pk_rule_ids = {hit["rule_id"] for hit in pair["pk"]["hits"]}
    pd_rule_ids = {hit["rule_id"] for hit in pair["pd"]["hits"]}

    return pk_rule_ids, pd_rule_ids


def test_pk_domain_excludes_pk_to_pd_composite_output() -> None:
    pk_rule_ids, pd_rule_ids = _pair_rule_ids(
        ["methadone", "clarithromycin"],
        domain="pk",
    )

    assert "PK_CYP3A4_STRONG_INHIB" in pk_rule_ids
    assert "COMP_PK_UP_CNS_DEP" not in pd_rule_ids
    assert pd_rule_ids == set()


def test_all_domain_keeps_pk_to_pd_composite_output() -> None:
    pk_rule_ids, pd_rule_ids = _pair_rule_ids(
        ["methadone", "clarithromycin"],
        domain="all",
    )

    assert "PK_CYP3A4_STRONG_INHIB" in pk_rule_ids
    assert "COMP_PK_UP_CNS_DEP" in pd_rule_ids