from __future__ import annotations

from core.enums import Domain, RuleClass, Severity
from core.models import Drug, Facts, PairReport, PDEffect, RuleHit
from reasoning.combine import build_regimen_summary


def test_regimen_summary_detects_repeated_pd_stack() -> None:
    facts = Facts(
        drugs={
            "a": Drug("a", "Drug A", None, "wide"),
            "b": Drug("b", "Drug B", None, "wide"),
            "c": Drug("c", "Drug C", None, "wide"),
        },
        pd_effects={
            "a": [PDEffect("nausea", "increase", "medium")],
            "b": [PDEffect("nausea", "increase", "high")],
            "c": [PDEffect("CNS_depression", "increase", "medium")],
        },
    )

    summary = build_regimen_summary(facts, [])

    assert summary["n_drugs"] == 3
    assert summary["pairwise_hit_count"] == 0

    nausea_stack = next(
        s for s in summary["pd_stacks"] if s["effect_id"] == "nausea"
    )

    assert nausea_stack["label"] == "nausea/GI intolerance"
    assert nausea_stack["count"] == 2
    assert nausea_stack["max_magnitude"] == "high"
    assert [d["drug_name"] for d in nausea_stack["drugs"]] == ["Drug B", "Drug A"]


def test_regimen_summary_escalates_three_drug_cns_stack() -> None:
    facts = Facts(
        drugs={
            "a": Drug("a", "Drug A", None, "wide"),
            "b": Drug("b", "Drug B", None, "wide"),
            "c": Drug("c", "Drug C", None, "wide"),
        },
        pd_effects={
            "a": [PDEffect("CNS_depression", "increase", "medium")],
            "b": [PDEffect("CNS_depression", "increase", "high")],
            "c": [PDEffect("CNS_depression", "increase", "medium")],
        },
    )

    summary = build_regimen_summary(facts, [])

    assert summary["overall_severity"] == Severity.contraindicated
    assert summary["overall_rule_class"] == RuleClass.avoid
    assert summary["regimen_flags"]

    flag = summary["regimen_flags"][0]
    assert flag["type"] == "PD_STACK"
    assert flag["effect_id"] == "CNS_depression"
    assert flag["count"] == 3


def test_regimen_summary_includes_hit_counts_and_top_pairs() -> None:
    facts = Facts(
        drugs={
            "a": Drug("a", "Drug A", None, "wide"),
            "b": Drug("b", "Drug B", None, "wide"),
        }
    )

    hit = RuleHit(
        rule_id="TEST_PD",
        name="Test PD",
        domain=Domain.PD,
        severity=Severity.major,
        rule_class=RuleClass.adjust_monitor,
        inputs={"A": "a", "B": "b"},
    )

    reports = [
        PairReport(
            drug_1="a",
            drug_2="b",
            overall_severity=Severity.major,
            overall_rule_class=RuleClass.adjust_monitor,
            pk_hits=[],
            pd_hits=[hit],
            pk_summary=None,
        )
    ]

    summary = build_regimen_summary(facts, reports)

    assert summary["pair_count_with_hits"] == 1
    assert summary["pairwise_hit_count"] == 1
    assert summary["hit_counts"]["total"] == 1
    assert summary["hit_counts"]["pk"] == 0
    assert summary["hit_counts"]["pd"] == 1
    assert summary["hit_counts"]["by_severity"] == {"major": 1}
    assert summary["hit_counts"]["by_class"] == {"adjust_monitor": 1}

    assert summary["top_pairs"][0]["drug_1"]["name"] == "Drug A"
    assert summary["top_pairs"][0]["drug_2"]["name"] == "Drug B"
    assert summary["top_pairs"][0]["total_hits"] == 1