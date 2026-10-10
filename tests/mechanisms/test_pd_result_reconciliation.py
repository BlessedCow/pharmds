from __future__ import annotations

from dataclasses import replace

import pytest

from app.service import analyze_names
from core.enums import Domain, RuleClass, Severity
from core.mechanisms.aggregation import AGGREGATE_SHARED_PD_EFFECT
from core.mechanisms.result_summary import (
    RESULT_SOURCE_AGGREGATE,
    RESULT_SOURCE_RULE,
    build_public_result_summaries,
)
from core.models import PairReport, RuleHit
from tests.mechanisms.support import pipeline_for


def _qt_report(
    *,
    rule_id: str = "PD_QT_ADDITIVE",
    effect_id: str | None = "QT_prolongation",
    first: str = "clarithromycin",
    second: str = "ondansetron",
) -> PairReport:
    hit = RuleHit(
        rule_id=rule_id,
        name="Additive QT prolongation",
        domain=Domain.PD,
        severity=Severity.caution,
        rule_class=RuleClass.caution,
        inputs={"A": first, "B": second, "effect_id": effect_id},
    )
    return PairReport(
        drug_1="clarithromycin",
        drug_2="ondansetron",
        overall_severity=Severity.caution,
        overall_rule_class="caution",
        pd_hits=[hit],
    )


@pytest.mark.parametrize(
    ("names", "effect"),
    [
        (["clarithromycin", "ondansetron"], "QT"),
        (["ondansetron", "clarithromycin"], "QT"),
        (["warfarin", "fluoxetine"], "bleeding"),
        (["alcohol", "clonazepam"], "respiratory depression"),
    ],
)
def test_curated_pd_rule_covers_matching_shared_effect(
    names: list[str], effect: str
) -> None:
    result = analyze_names(names, as_json_payload=True)
    assert result.ok
    assert any(
        item["aggregate"]["aggregate_type"] == AGGREGATE_SHARED_PD_EFFECT
        for item in result.payload["mechanism_pipeline"]["aggregate_concern_summaries"]
    )
    summaries = result.payload["public_result_summaries"]
    assert not any(
        item["source"] == RESULT_SOURCE_AGGREGATE
        and effect.lower() in item["title"].lower()
        for item in summaries
    )
    assert any(item["source"] == RESULT_SOURCE_RULE for item in summaries)


def test_shared_effect_remains_without_matching_curated_identity() -> None:
    pipeline = pipeline_for(["clarithromycin", "ondansetron"])
    for report in (
        _qt_report(rule_id="PD_UNRELATED"),
        _qt_report(effect_id=None),
        _qt_report(effect_id="sedation"),
        _qt_report(first="other_drug"),
    ):
        summaries = build_public_result_summaries(pipeline, [report])
        assert any(
            item.source == RESULT_SOURCE_AGGREGATE
            and item.title == "Shared QT prolongation concern"
            for item in summaries
        )


def test_partially_covered_three_drug_effect_stays_visible() -> None:
    pipeline = pipeline_for(["clarithromycin", "ondansetron"])
    qt = next(
        item
        for item in pipeline.aggregate_concern_summaries
        if item.aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT
        and item.aggregate.effect_id == "QT_prolongation"
    )
    third_pair = replace(qt.aggregate.members[0], object_drug="fluconazole")
    expanded = replace(
        qt,
        aggregate=replace(
            qt.aggregate,
            drugs=("clarithromycin", "fluconazole", "ondansetron"),
            members=(*qt.aggregate.members, third_pair),
        ),
    )
    pipeline = replace(pipeline, aggregate_concern_summaries=(expanded,))
    summaries = build_public_result_summaries(pipeline, [_qt_report()])
    assert {item.source for item in summaries} == {
        RESULT_SOURCE_AGGREGATE,
        RESULT_SOURCE_RULE,
    }


@pytest.mark.parametrize("status", ["partial", "missing", "disputed", "conflicting"])
def test_evidence_limitations_remain_public_with_matching_rule(status: str) -> None:
    pipeline = pipeline_for(["clarithromycin", "ondansetron"])
    qt = next(
        item
        for item in pipeline.aggregate_concern_summaries
        if item.aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT
        and item.aggregate.effect_id == "QT_prolongation"
    )
    assert qt.evidence_summary is not None
    limited = replace(
        qt,
        evidence_summary=replace(qt.evidence_summary, overall_evidence_status=status),
    )
    pipeline = replace(pipeline, aggregate_concern_summaries=(limited,))
    summaries = build_public_result_summaries(pipeline, [_qt_report()])
    assert summaries[0].source == RESULT_SOURCE_AGGREGATE
    assert summaries[0].evidence_label == status
