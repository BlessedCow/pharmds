from core.enums import Domain, RuleClass, Severity
from core.models import Facts
from core.regimen import RegimenDose
from rules.engine import Rule, evaluate_rule


def _rule(dose: dict) -> Rule:
    return Rule(
        id="TEST_DOSE",
        name="Dose guard",
        domain=Domain.PD,
        severity=Severity.caution,
        rule_class=RuleClass.adjust_monitor,
        logic={
            "drug_pair": {"a": "lorazepam", "b": "other"},
            "dose": dose,
        },
        explanation_template="Test dose guard.",
        actions=[],
        tags=[],
        references=[],
    )


def test_scheduled_daily_guard_distinguishes_qam_from_high_frequency() -> None:
    rule = _rule(
        {"drug": "A", "unit": "mg", "min_scheduled_daily": 4}
    )
    facts = Facts(
        regimen_doses={
            "lorazepam": RegimenDose(2, "mg", frequency="QAM")
        }
    )
    assert evaluate_rule(rule, facts, "lorazepam", "other") is None

    facts.regimen_doses["lorazepam"] = RegimenDose(
        2,
        "mg",
        frequency="Q4H",
    )
    assert evaluate_rule(rule, facts, "lorazepam", "other") is not None


def test_prn_guard_uses_prn_ceiling_not_scheduled_daily_dose() -> None:
    facts = Facts(
        regimen_doses={
            "lorazepam": RegimenDose(
                2,
                "mg",
                frequency="Q4H",
                schedule_type="prn",
            )
        }
    )
    scheduled_rule = _rule(
        {"drug": "A", "unit": "mg", "min_scheduled_daily": 4}
    )
    assert (
        evaluate_rule(scheduled_rule, facts, "lorazepam", "other") is None
    )

    prn_rule = _rule(
        {
            "drug": "A",
            "unit": "mg",
            "schedule_type": "prn",
            "min_prn_max_daily": 10,
        }
    )
    assert evaluate_rule(prn_rule, facts, "lorazepam", "other") is not None


def test_timing_guard_distinguishes_tid_from_q8h() -> None:
    facts = Facts(
        regimen_doses={
            "lorazepam": RegimenDose(2, "mg", frequency="TID")
        }
    )
    interval_rule = _rule(
        {
            "drug": "A",
            "timing_type": "fixed_interval",
            "interval_hours": 8,
            "around_the_clock": True,
        }
    )
    assert evaluate_rule(interval_rule, facts, "lorazepam", "other") is None

    facts.regimen_doses["lorazepam"] = RegimenDose(
        2,
        "mg",
        frequency="Q8H",
    )
    assert evaluate_rule(interval_rule, facts, "lorazepam", "other") is not None


def test_daypart_guard_distinguishes_qam_from_qhs() -> None:
    bedtime_rule = _rule(
        {
            "drug": "A",
            "timing_type": "daypart",
            "daypart": "bedtime",
        }
    )
    facts = Facts(
        regimen_doses={
            "lorazepam": RegimenDose(2, "mg", frequency="QAM")
        }
    )
    assert evaluate_rule(bedtime_rule, facts, "lorazepam", "other") is None

    facts.regimen_doses["lorazepam"] = RegimenDose(
        2,
        "mg",
        frequency="QHS",
    )
    assert evaluate_rule(bedtime_rule, facts, "lorazepam", "other") is not None
