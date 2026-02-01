from __future__ import annotations

import app.cli as cli_mod
from app.cli import connect, resolve_drug_ids, load_facts, RULE_DIR, DB_PATH
from rules.engine import evaluate_all, load_rules


def _run_filtered(drugs: list[str], domain: str):
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, drugs)
    facts = load_facts(conn, drug_ids, patient_flags={})

    rules_all = load_rules(RULE_DIR)
    selected = cli_mod._parse_domain_selection(domain)
    rules = cli_mod.filter_rules_for_selected_domains(rules_all, selected)

    hits = evaluate_all(rules, facts, drug_ids)
    return hits


def test_domain_pgp_fires_pgp_inhib_digoxin_verapamil():
    hits = _run_filtered(["digoxin", "verapamil"], "pgp")
    assert any(h.rule_id == "PK_PGP_INHIB_DIGOXIN" for h in hits)


def test_domain_cyp_excludes_pgp_digoxin_verapamil():
    hits = _run_filtered(["digoxin", "verapamil"], "cyp")
    assert not any(h.rule_id == "PK_PGP_INHIB_DIGOXIN" for h in hits)


def test_domain_pd_fires_qt_only_citalopram_ondansetron():
    hits = _run_filtered(["citalopram", "ondansetron"], "pd")
    assert any(h.rule_id == "PD_QT_ADDITIVE" for h in hits)


def test_domain_pgp_fires_pgp_induc_digoxin_rifampin():
    hits = _run_filtered(["digoxin", "rifampin"], "pgp")
    assert any(h.rule_id == "PK_PGP_INDUC_DIGOXIN" for h in hits)
