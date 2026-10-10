from app.cli import RULE_DIR
from core.mechanisms import run_mechanism_pipeline
from rules.engine import evaluate_all, load_rules
from tests.mechanisms.support import load_drug_facts


def _load_context(names: list[str]):
    drug_ids, facts = load_drug_facts(
        names,
        patient_flags={"qt_risk": False, "bleeding_risk": False},
    )
    rules = load_rules(RULE_DIR)
    return facts, rules, drug_ids


def _run_normal_analysis(names: list[str]):
    facts, rules, drug_ids = _load_context(names)
    return evaluate_all(rules, facts, drug_ids)


def _rule_ids(hits) -> list[str]:
    return sorted(hit.rule_id for hit in hits)


def _assert_pipeline_does_not_change_hits(names: list[str]):
    facts, rules, drug_ids = _load_context(names)

    before = evaluate_all(rules, facts, drug_ids)
    pipeline = run_mechanism_pipeline(drug_ids, facts)
    after = evaluate_all(rules, facts, drug_ids)

    assert pipeline.effects
    assert _rule_ids(after) == _rule_ids(before)


def test_mechanism_pipeline_does_not_change_bupropion_vortioxetine_hits():
    hits = _run_normal_analysis(["bupropion", "vortioxetine"])
    rids = set(_rule_ids(hits))

    assert "PK_CYP2D6_INHIB_SUBSTRATE" in rids

    _assert_pipeline_does_not_change_hits(["bupropion", "vortioxetine"])


def test_mechanism_pipeline_does_not_change_fluconazole_vortioxetine_hits():
    before = _run_normal_analysis(["fluconazole", "vortioxetine"])

    _assert_pipeline_does_not_change_hits(["fluconazole", "vortioxetine"])

    after = _run_normal_analysis(["fluconazole", "vortioxetine"])
    assert _rule_ids(after) == _rule_ids(before)


def test_mechanism_pipeline_does_not_change_clarithromycin_digoxin_hits():
    hits = _run_normal_analysis(["clarithromycin", "digoxin"])
    rids = set(_rule_ids(hits))

    assert "PK_PGP_INHIB_DIGOXIN" in rids

    _assert_pipeline_does_not_change_hits(["clarithromycin", "digoxin"])


def test_mechanism_pipeline_does_not_change_no_hit_baseline():
    before = _run_normal_analysis(["clarithromycin", "fluconazole"])

    _assert_pipeline_does_not_change_hits(["clarithromycin", "fluconazole"])

    after = _run_normal_analysis(["clarithromycin", "fluconazole"])
    assert _rule_ids(after) == _rule_ids(before)
