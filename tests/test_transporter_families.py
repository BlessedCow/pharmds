from __future__ import annotations

from pathlib import Path

from app.cli import connect, resolve_drug_ids, load_facts, RULE_DIR, DB_PATH
from rules.engine import load_rules, evaluate_all


def test_transporter_family_rule_matches_pgp_roles():
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, ["digoxin", "verapamil"])
    facts = load_facts(conn, drug_ids, patient_flags={})

    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)

    assert any(h.rule_id == "PK_PGP_INHIB_DIGOXIN" for h in hits)
