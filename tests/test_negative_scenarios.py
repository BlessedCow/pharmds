"""Negative / non-trigger tests.

These tests exist to reduce false positives ("alert fatigue"). They assert that
rules do NOT fire when mechanisms/overlaps are absent or when the "wrong" rule
could be tempting.
"""

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


def _rule_ids(hits):
    return {h.rule_id for h in hits}


def test_negative_no_interaction_midazolam_fluconazole():
    """Fluconazole is not a CYP3A4 strong inhibitor in seed data; no PD overlap either."""
    _, hits = _run(["midazolam", "fluconazole"])
    assert hits == []


def test_negative_no_interaction_clopidogrel_clarithromycin():
    """Clarithromycin should not be treated as a CYP2C19 inhibitor for clopidogrel activation."""
    _, hits = _run(["clopidogrel", "clarithromycin"])
    assert hits == []


def test_negative_no_interaction_warfarin_clarithromycin():
    """Clarithromycin should not trip the CYP2C9 inhibition warfarin rule in current seed data."""
    _, hits = _run(["warfarin", "clarithromycin"])
    assert hits == []


def test_negative_no_interaction_digoxin_fluconazole():
    """Digoxin is a P-gp substrate, but fluconazole is not a P-gp inhibitor/inducer in seed data."""
    _, hits = _run(["digoxin", "fluconazole"])
    assert hits == []


def test_negative_no_qt_hit_citalopram_sertraline():
    """Only citalopram has QT liability in seed data; this pair can still be serotonergic."""
    _, hits = _run(["citalopram", "sertraline"])
    assert "PD_QT_ADDITIVE" not in _rule_ids(hits)


def test_negative_no_bradycardia_hit_propranolol_tizanidine():
    """Only propranolol has bradycardia liability in seed data."""
    _, hits = _run(["propranolol", "tizanidine"])
    assert "PD_BRADYCARDIA_ADDITIVE" not in _rule_ids(hits)
    assert hits == []


def test_negative_desvenlafaxine_not_serotonergic_overlap():
    """Desvenlafaxine is modeled under serotonin_syndrome (not serotonergic overlap) in seed."""
    _, hits = _run(["desvenlafaxine", "sertraline"])
    rids = _rule_ids(hits)
    assert "PD_SEROTONIN_SYNDROME_ADDITIVE" in rids
    assert "PD_SEROTONERGIC_ADDITIVE" not in rids


def test_negative_no_cyp3a4_strong_inhib_quetiapine_fluconazole():
    """Quetiapine is CYP3A4 substrate, but fluconazole is not a strong CYP3A4 inhibitor in seed."""
    _, hits = _run(["quetiapine", "fluconazole"])
    assert hits == []


def test_negative_pgp_induction_not_inhibition_digoxin_rifampin():
    """Rifampin should induce (not inhibit) P-gp for digoxin in seed data."""
    _, hits = _run(["digoxin", "rifampin"])
    rids = _rule_ids(hits)
    assert "PK_PGP_INDUC_DIGOXIN" in rids
    assert "PK_PGP_INHIB_DIGOXIN" not in rids


def test_negative_cyp3a4_induction_not_inhibition_midazolam_rifampin():
    """Rifampin should induce (not inhibit) CYP3A4 for midazolam in seed data."""
    _, hits = _run(["midazolam", "rifampin"])
    rids = _rule_ids(hits)
    assert "PK_CYP3A4_STRONG_INDUC" in rids
    assert "PK_CYP3A4_STRONG_INHIB" not in rids

def test_negative_no_bcrp_hit_rosuvastatin_fluconazole():
    """Fluconazole should not be treated as a BCRP inhibitor in seed data."""
    _, hits = _run(["rosuvastatin", "fluconazole"])
    assert "PK_BCRP_INHIB_SUBSTRATE" not in _rule_ids(hits)

def test_negative_no_oatp_hit_rosuvastatin_fluconazole():
    """Fluconazole is not modeled as an OATP inhibitor in seed data."""
    _, hits = _run(["rosuvastatin", "fluconazole"])
    assert "PK_OATP_INHIB" not in _rule_ids(hits)