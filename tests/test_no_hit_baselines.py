from __future__ import annotations

from app.service import analyze_names


def _pair_reports(result):
    assert result.ok
    return result.payload["pair_reports"]


def _regimen_summary(result) -> dict:
    assert result.ok
    return result.payload.get("regimen_summary") or {}


def _rule_ids(result) -> set[str]:
    ids: set[str] = set()

    for pair in _pair_reports(result):
        for hit in pair.pk_hits:
            ids.add(hit.rule_id)
        for hit in pair.pd_hits:
            ids.add(hit.rule_id)

    return ids


def _pd_stack_ids(result) -> set[str]:
    summary = _regimen_summary(result)
    return {s["effect_id"] for s in summary.get("pd_stacks", [])}


def test_single_nausea_contributor_does_not_create_nausea_stack() -> None:
    result = analyze_names(["vortioxetine", "rosuvastatin"])

    assert "PD_NAUSEA_ADDITIVE" not in _rule_ids(result)
    assert "nausea" not in _pd_stack_ids(result)


def test_non_qt_pair_does_not_create_qt_additive_warning() -> None:
    result = analyze_names(["bupropion", "rosuvastatin"])

    assert "PD_QT_ADDITIVE" not in _rule_ids(result)
    assert "QT_prolongation" not in _pd_stack_ids(result)


def test_serotonin_warning_requires_serotonergic_burden() -> None:
    result = analyze_names(["bupropion", "methylphenidate"])

    assert "PD_SEROTONERGIC_ADDITIVE" not in _rule_ids(result)
    assert "serotonergic" not in _pd_stack_ids(result)


def test_cns_stack_does_not_escalate_with_only_two_contributors() -> None:
    result = analyze_names(["quetiapine", "hydroxyzine"])
    summary = _regimen_summary(result)

    flags = summary.get("regimen_flags", [])
    cns_escalation_flags = [
        flag
        for flag in flags
        if flag.get("type") == "PD_STACK"
        and flag.get("effect_id") == "CNS_depression"
    ]

    assert cns_escalation_flags == []


def test_three_drug_regimen_without_repeated_medium_pd_effects() -> None:
    result = analyze_names(["rosuvastatin", "lisinopril", "amoxicillin"])
    summary = _regimen_summary(result)

    assert summary.get("regimen_flags", []) == []
    assert summary.get("pd_stacks", []) == []