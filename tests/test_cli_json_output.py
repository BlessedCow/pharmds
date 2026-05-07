from __future__ import annotations

import json

import app.cli as cli_mod
from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from app.json_output import build_json_payload
from reasoning.combine import build_regimen_summary
from rules.composite_rules import apply_composites
from rules.engine import evaluate_all, load_rules


def _build_payload(drugs: list[str], domain: str = "all"):
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, drugs)
    patient_flags = {}
    facts = load_facts(conn, drug_ids, patient_flags=patient_flags)

    rules_all = load_rules(RULE_DIR)
    selected = cli_mod._parse_domain_selection(domain)
    rules = cli_mod.filter_rules_for_selected_domains(rules_all, selected)
    hits = evaluate_all(rules, facts, drug_ids)
    hits = apply_composites(facts, hits)

    templates = {r.id: r.explanation_template for r in rules}
    reports = cli_mod._build_reports_for_all_pairs(facts, hits, templates, drug_ids)

    regimen_summary = None
    if len(drug_ids) >= 3:
        regimen_summary = build_regimen_summary(facts, reports)

    payload = build_json_payload(
        facts=facts,
        reports=reports,
        templates=templates,
        selected_domains=selected,
        input_drug_names=drugs,
        patient_flags=patient_flags,
        regimen_summary=regimen_summary,
    )
    return payload


def test_json_payload_includes_regimen_summary_for_three_drugs():
    payload = _build_payload(
        ["quetiapine", "hydroxyzine", "trazodone"],
        domain="all",
    )

    assert "regimen_summary" in payload
    summary = payload["regimen_summary"]

    assert summary["n_drugs"] == 3
    assert "hit_counts" in summary
    assert "pd_stacks" in summary
    assert "top_pairs" in summary


def test_json_payload_is_valid_and_versioned():
    payload = _build_payload(["citalopram", "ondansetron"], domain="pd")
    s = json.dumps(payload)
    obj = json.loads(s)

    assert obj["schema_version"] == "1.0"
    assert obj["input"]["selected_domains"] == ["pd"]
    assert len(obj["pairs"]) >= 1


def test_json_payload_contains_expected_fields_for_pk_pair():
    payload = _build_payload(["quetiapine", "clarithromycin"], domain="cyp")
    pair = payload["pairs"][0]

    assert "overall" in pair
    assert "pk" in pair and "hits" in pair["pk"]
    assert isinstance(pair["pk"]["hits"], list)

    assert any(
        (h.get("explanation") or h.get("rationale"))
        for h in pair["pk"]["hits"]
    )


def test_json_hits_include_normalized_rationales():
    payload = _build_payload(["fluoxetine", "bupropion"], domain="cyp")

    hits = []
    for pair in payload["pairs"]:
        hits.extend(pair["pk"]["hits"])
        hits.extend(pair["pd"]["hits"])

    assert hits
    assert all("severity_rationale" in h for h in hits)
    assert all("action_rationale" in h for h in hits)
    assert any("Caution because" in h["severity_rationale"] for h in hits)
    assert any("Adjust/monitor action" in h["action_rationale"] for h in hits)