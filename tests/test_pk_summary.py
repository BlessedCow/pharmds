from __future__ import annotations

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from core.enums import Domain, RuleClass, Severity
from core.models import Facts, RuleHit
from reasoning.combine import build_pair_reports
from rules.engine import evaluate_all, load_rules


def test_pk_summary_exposure_increase_digoxin_verapamil():
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, ["digoxin", "verapamil"])
    facts = load_facts(conn, drug_ids, patient_flags={})

    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)

    templates = {r.id: r.explanation_template for r in rules}
    reports = build_pair_reports(facts, hits, templates)

    assert reports
    rep = reports[0]
    assert rep.pk_summary == "exposure_increase"


def test_pk_summary_mixed_synthetic():
    facts = Facts()

    hits = [
        RuleHit(
            rule_id="PK_FAKE_INCREASE",
            name="Fake increase",
            domain=Domain.PK,
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
            inputs={"A": "a", "B": "b"},
            tags=["exposure_increase"],
        ),
        RuleHit(
            rule_id="PK_FAKE_DECREASE",
            name="Fake decrease",
            domain=Domain.PK,
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
            inputs={"A": "a", "B": "b"},
            tags=["exposure_decrease"],
        ),
    ]

    reports = build_pair_reports(facts, hits, rule_templates={})
    assert reports
    assert reports[0].pk_summary == "mixed (increase + decrease mechanisms present)"
