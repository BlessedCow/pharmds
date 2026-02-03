from __future__ import annotations

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from rules.engine import evaluate_all, load_rules


def _run(drugs: list[str]):
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, drugs)
    facts = load_facts(conn, drug_ids, patient_flags={})
    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)
    return facts, hits


def test_pk_cyp3a4_strong_inhib_quetiapine_clarithro():
    _, hits = _run(["quetiapine", "clarithromycin"])
    assert any(
        h.rule_id == "PK_CYP3A4_STRONG_INHIB" and h.inputs["A"] == "quetiapine"
        for h in hits
    )


def test_pk_cyp3a4_strong_induc_midazolam_rifampin():
    _, hits = _run(["midazolam", "rifampin"])
    assert any(
        h.rule_id == "PK_CYP3A4_STRONG_INDUC" and h.inputs["A"] == "midazolam"
        for h in hits
    )


def test_pk_prodrug_activation_clopidogrel_fluconazole():
    _, hits = _run(["clopidogrel", "fluconazole"])
    assert any(
        h.rule_id == "PK_CYP2C19_INHIB_CLOPIDOGREL" and h.inputs["A"] == "clopidogrel"
        for h in hits
    )


def test_pk_pgp_digoxin_clarithro():
    _, hits = _run(["digoxin", "clarithromycin"])
    assert any(
        h.rule_id == "PK_PGP_INHIB_DIGOXIN" and h.inputs["A"] == "digoxin" for h in hits
    )


def test_pd_qt_no_duplicates_citalopram_ondansetron():
    _, hits = _run(["citalopram", "ondansetron"])
    qt_hits = [h for h in hits if h.rule_id == "PD_QT_ADDITIVE"]
    assert len(qt_hits) == 1
