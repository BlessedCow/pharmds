# known interaction scenarios

from __future__ import annotations

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from rules.engine import evaluate_all, load_rules


def test_warfarin_fluconazole_flags_major_or_higher():
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, ["warfarin", "fluconazole"])
    facts = load_facts(conn, drug_ids, patient_flags={})
    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)

    # Expect at least one hit involving warfarin as A and fluconazole as B on CYP2C9 inhibition pattern
    assert any(h.rule_id == "PK_CYP2C9_INHIB_WARFARIN" for h in hits)


def test_qt_overlap_citalopram_ondansetron():
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, ["citalopram", "ondansetron"])
    facts = load_facts(conn, drug_ids, patient_flags={})
    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)
    assert any(h.rule_id == "PD_QT_ADDITIVE" for h in hits)
