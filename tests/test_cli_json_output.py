from __future__ import annotations

import json
import sys

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

def _assert_pair_json_contract(pair: dict):
    assert set(pair) == {
        "drug_1",
        "drug_2",
        "overall",
        "pk",
        "pd",
    }
    assert set(pair["drug_1"]) == {"id", "name"}
    assert set(pair["drug_2"]) == {"id", "name"}
    assert set(pair["overall"]) == {"severity", "class"}
    assert set(pair["pk"]) == {"summary", "hits"}
    assert set(pair["pd"]) == {"hits"}
    assert isinstance(pair["pk"]["hits"], list)
    assert isinstance(pair["pd"]["hits"], list)


def _assert_hit_json_contract(hit: dict):
    assert set(hit) == {
        "rule_id",
        "name",
        "domain",
        "severity",
        "class",
        "severity_rationale",
        "action_rationale",
        "inputs",
        "tags",
        "explanation",
        "rationale",
        "actions",
        "references",
        "A",
        "B",
    }
    assert set(hit["A"]) == {"id", "name"}
    assert set(hit["B"]) == {"id", "name"}
    assert isinstance(hit["inputs"], dict)
    assert isinstance(hit["tags"], list)
    assert isinstance(hit["rationale"], list)
    assert isinstance(hit["actions"], list)
    assert isinstance(hit["references"], list)


def test_cli_json_payload_contract_for_two_drug_pair():
    payload = _build_payload(["quetiapine", "clarithromycin"], domain="cyp")

    assert set(payload) == {
        "schema_version",
        "input",
        "pairs",
    }
    assert set(payload["input"]) == {
        "drug_names",
        "selected_domains",
        "patient_flags",
    }
    assert isinstance(payload["pairs"], list)
    assert payload["pairs"]

    pair = payload["pairs"][0]
    _assert_pair_json_contract(pair)

    assert pair["pk"]["hits"]
    _assert_hit_json_contract(pair["pk"]["hits"][0])


def test_cli_json_regimen_summary_contract_for_three_drugs():
    payload = _build_payload(
        ["quetiapine", "hydroxyzine", "trazodone"],
        domain="all",
    )

    assert set(payload) == {
        "schema_version",
        "input",
        "pairs",
        "regimen_summary",
    }

    summary = payload["regimen_summary"]

    assert set(summary) == {
        "n_drugs",
        "overall_severity",
        "overall_rule_class",
        "overview",
        "pairwise_summary",
        "cumulative_concern_summary",
        "regimen_flags",
        "pd_stacks",
        "pair_count_with_hits",
        "pairwise_hit_count",
        "hit_counts",
        "top_pairs",
    }

    assert set(summary["hit_counts"]) == {
        "total",
        "pk",
        "pd",
        "by_severity",
        "by_class",
    }
    assert isinstance(summary["regimen_flags"], list)
    assert isinstance(summary["pd_stacks"], list)
    assert isinstance(summary["top_pairs"], list)

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

def test_cli_json_shortcut_outputs_json(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--json",
        ],
    )

    cli_mod.main()

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert payload["schema_version"] == "1.0"
    assert payload["input"]["drug_names"] == ["clarithromycin", "fluconazole"]

def test_cli_format_json_outputs_public_pair_contract(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "quetiapine",
            "clarithromycin",
            "--format",
            "json",
            "--domain",
            "cyp",
        ],
    )

    cli_mod.main()

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert set(payload) == {
        "schema_version",
        "input",
        "pairs",
    }
    assert payload["schema_version"] == "1.0"
    assert payload["input"]["drug_names"] == [
        "quetiapine",
        "clarithromycin",
    ]
    assert payload["input"]["selected_domains"] == ["cyp"]
    assert payload["pairs"]

    pair = payload["pairs"][0]
    _assert_pair_json_contract(pair)


def test_cli_format_json_outputs_regimen_summary_contract(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "quetiapine",
            "hydroxyzine",
            "trazodone",
            "--format",
            "json",
        ],
    )

    cli_mod.main()

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert set(payload) == {
        "schema_version",
        "input",
        "pairs",
        "regimen_summary",
    }
    assert set(payload["regimen_summary"]) == {
        "n_drugs",
        "overall_severity",
        "overall_rule_class",
        "overview",
        "pairwise_summary",
        "cumulative_concern_summary",
        "regimen_flags",
        "pd_stacks",
        "pair_count_with_hits",
        "pairwise_hit_count",
        "hit_counts",
        "top_pairs",
    }

def test_cli_format_json_show_evidence_gaps_outputs_json(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--format",
            "json",
            "--show-evidence-gaps",
        ],
    )

    cli_mod.main()

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert "total_pd_effects" in payload
    assert "gap_count" in payload
    assert "coverage_counts" in payload
    assert "confidence_counts" in payload
    assert "gaps_by_pd_effect" in payload
    assert "gaps_by_drug" in payload
    assert "gaps_by_source_type" in payload
    assert "items" in payload
    assert "backfill_plan" in payload

    assert "PD Effect Evidence Gaps" not in out
    
def test_cli_format_json_show_aggregate_evidence_outputs_json(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--format",
            "json",
            "--show-aggregate-evidence",
        ],
    )

    cli_mod.main()

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert set(payload) == {"aggregate_evidence_summaries"}
    assert payload["aggregate_evidence_summaries"]
    assert "Aggregate Evidence Summary" not in out


def test_cli_format_json_show_aggregate_summaries_outputs_json(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--format",
            "json",
            "--show-aggregate-summaries",
        ],
    )

    cli_mod.main()

    out = capsys.readouterr().out
    payload = json.loads(out)

    assert set(payload) == {"aggregate_concern_summaries"}
    assert payload["aggregate_concern_summaries"]
    assert "Aggregate Concern Summaries" not in out