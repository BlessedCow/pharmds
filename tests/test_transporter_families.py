from __future__ import annotations

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from rules.engine import evaluate_all, load_rules


def test_transporter_family_rule_matches_pgp_roles():
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, ["digoxin", "verapamil"])
    facts = load_facts(conn, drug_ids, patient_flags={})

    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)

    assert any(h.rule_id == "PK_PGP_INHIB_DIGOXIN" for h in hits)
