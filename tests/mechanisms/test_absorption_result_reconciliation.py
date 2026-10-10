from __future__ import annotations

from dataclasses import replace

import pytest

from app.service import analyze_names
from core.enums import Domain, RuleClass, Severity
from core.mechanisms.result_summary import (
    RESULT_SOURCE_AGGREGATE,
    RESULT_SOURCE_RULE,
    build_public_result_summaries,
)
from core.models import PairReport, RuleHit
from tests.mechanisms.support import pipeline_for


@pytest.mark.parametrize(
    "names",
    [
        ["doxycycline", "calcium carbonate"],
        ["calcium carbonate", "doxycycline"],
    ],
)
def test_curated_absorption_rule_is_presented_once(names: list[str]) -> None:
    result = analyze_names(names, as_json_payload=True)
    assert result.ok
    summaries = result.payload["public_result_summaries"]
    matching = [
        item
        for item in summaries
        if set(item["drugs"]) == {"doxycycline", "calcium_carbonate"}
    ]
    assert len(matching) == 1
    assert matching[0]["source"] == RESULT_SOURCE_RULE
    assert matching[0]["severity_label"] == "major"
    assert result.payload["mechanism_pipeline"]["candidates"]


def test_absorption_summary_remains_without_matching_curated_rule() -> None:
    pipeline = pipeline_for(["doxycycline", "calcium carbonate"])
    summaries = build_public_result_summaries(pipeline)
    assert any(item.source == RESULT_SOURCE_AGGREGATE for item in summaries)


def test_unrelated_rule_does_not_hide_absorption_mechanism() -> None:
    pipeline = pipeline_for(["doxycycline", "calcium carbonate"])
    hit = RuleHit(
        rule_id="PK_UNRELATED",
        name="Unrelated rule",
        domain=Domain.PK,
        severity=Severity.caution,
        rule_class=RuleClass.caution,
        inputs={"A": "doxycycline", "B": "calcium_carbonate"},
    )
    report = PairReport(
        drug_1="doxycycline",
        drug_2="calcium_carbonate",
        overall_severity=Severity.caution,
        overall_rule_class="caution",
        pk_hits=[hit],
    )
    summaries = build_public_result_summaries(pipeline, [report])
    assert {item.source for item in summaries} == {
        RESULT_SOURCE_AGGREGATE,
        RESULT_SOURCE_RULE,
    }


def test_multiple_effect_records_preserve_curated_absorption_coverage() -> None:
    pipeline = pipeline_for(["doxycycline", "calcium carbonate"])
    agent = next(
        effect
        for effect in pipeline.effects
        if effect.source_drug == "calcium_carbonate"
        and effect.evidence_refs
    )
    object_effect = next(
        effect
        for effect in pipeline.effects
        if effect.source_drug == "doxycycline"
        and effect.evidence_refs
    )
    unrelated_agent = replace(agent, evidence_refs=("PK_OTHER",))
    unrelated_object = replace(object_effect, evidence_refs=("PK_OTHER",))
    pipeline = replace(
        pipeline,
        effects=(*pipeline.effects, unrelated_agent, unrelated_object),
    )
    hit = RuleHit(
        rule_id="PK_DOXYCYCLINE_CALCIUM_CARBONATE",
        name="Doxycycline calcium chelation",
        domain=Domain.PK,
        severity=Severity.major,
        rule_class=RuleClass.caution,
        inputs={"A": "doxycycline", "B": "calcium_carbonate"},
    )
    report = PairReport(
        drug_1="doxycycline",
        drug_2="calcium_carbonate",
        overall_severity=Severity.major,
        overall_rule_class="caution",
        pk_hits=[hit],
    )
    summaries = build_public_result_summaries(pipeline, [report])
    assert len(summaries) == 1
    assert summaries[0].source == RESULT_SOURCE_RULE
