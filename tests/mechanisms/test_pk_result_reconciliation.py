from __future__ import annotations

from dataclasses import replace

import pytest

from app.service import analyze_names
from core.enums import Domain, RuleClass, Severity
from core.mechanisms.candidates import CANDIDATE_ENZYME_INDUCTION
from core.mechanisms.result_summary import (
    RESULT_SOURCE_AGGREGATE,
    RESULT_SOURCE_RULE,
    build_public_result_summaries,
)
from core.models import PairReport, RuleHit
from tests.mechanisms.support import pipeline_for


def _report(
    *,
    rule_id: str = "PK_CYP3A4_STRONG_INHIB",
    object_drug: str = "midazolam",
    precipitant_drug: str = "clarithromycin",
    target: str | None = "CYP3A4",
) -> PairReport:
    hit = RuleHit(
        rule_id=rule_id,
        name="Curated CYP3A4 rule",
        domain=Domain.PK,
        severity=Severity.major,
        rule_class=RuleClass.caution,
        inputs={"A": object_drug, "B": precipitant_drug, "enzyme_id": target},
    )
    return PairReport(
        drug_1="clarithromycin",
        drug_2="midazolam",
        overall_severity=Severity.major,
        overall_rule_class="caution",
        pk_hits=[hit],
    )


@pytest.mark.parametrize(
    "names",
    [
        ["clarithromycin", "midazolam"],
        ["midazolam", "clarithromycin"],
        ["bupropion", "vortioxetine"],
        ["vortioxetine", "bupropion"],
    ],
)
def test_curated_enzyme_rule_covers_public_exposure_summary(
    names: list[str],
) -> None:
    result = analyze_names(names, as_json_payload=True)
    assert result.ok
    payload = result.payload
    assert payload["mechanism_pipeline"]["aggregate_concerns"]
    summaries = payload["public_result_summaries"]
    assert not any(
        item["source"] == RESULT_SOURCE_AGGREGATE
        and "exposure increase" in item["title"]
        for item in summaries
    )
    expected_rule = (
        "PK_CYP3A4_STRONG_INHIB"
        if "midazolam" in names
        else "PK_CYP2D6_INHIB_SUBSTRATE"
    )
    assert expected_rule in {
        hit["rule_id"] for report in payload["pairs"] for hit in report["pk"]["hits"]
    }
    assert any(item["source"] == RESULT_SOURCE_RULE for item in summaries)


def test_missing_rule_or_structured_identity_retains_mechanism_summary() -> None:
    pipeline = pipeline_for(["clarithromycin", "midazolam"])
    assert any(
        item.source == RESULT_SOURCE_AGGREGATE
        for item in build_public_result_summaries(pipeline)
    )
    for report in (
        _report(rule_id="PK_UNRELATED"),
        _report(target=None),
        _report(target="CYP2D6"),
        _report(object_drug="clarithromycin", precipitant_drug="midazolam"),
    ):
        summaries = build_public_result_summaries(pipeline, [report])
        assert {item.source for item in summaries} == {
            RESULT_SOURCE_AGGREGATE,
            RESULT_SOURCE_RULE,
        }


def test_distinct_mechanism_in_same_aggregate_remains_visible() -> None:
    pipeline = pipeline_for(["clarithromycin", "midazolam"])
    summary = next(
        item
        for item in pipeline.aggregate_concern_summaries
        if item.aggregate.anchor == "midazolam"
        and "increase" in item.aggregate.aggregate_type
    )
    other_member = replace(
        summary.aggregate.members[0],
        candidate_type=CANDIDATE_ENZYME_INDUCTION,
    )
    mixed = replace(
        summary,
        aggregate=replace(
            summary.aggregate,
            members=(*summary.aggregate.members, other_member),
        ),
    )
    pipeline = replace(pipeline, aggregate_concern_summaries=(mixed,))
    summaries = build_public_result_summaries(pipeline, [_report()])
    assert {item.source for item in summaries} == {
        RESULT_SOURCE_AGGREGATE,
        RESULT_SOURCE_RULE,
    }


def test_rule_on_different_report_pair_cannot_cover_mechanism() -> None:
    pipeline = pipeline_for(["clarithromycin", "midazolam"])
    report = _report()
    report = replace(report, drug_2="quetiapine")
    summaries = build_public_result_summaries(pipeline, [report])
    assert any(item.source == RESULT_SOURCE_AGGREGATE for item in summaries)


@pytest.mark.parametrize(
    ("names", "rule_id", "direction"),
    [
        (["digoxin", "clarithromycin"], "PK_PGP_INHIB_DIGOXIN", "increase"),
        (["clarithromycin", "digoxin"], "PK_PGP_INHIB_DIGOXIN", "increase"),
        (["digoxin", "rifampin"], "PK_PGP_INDUC_DIGOXIN", "decrease"),
        (["rifampin", "digoxin"], "PK_PGP_INDUC_DIGOXIN", "decrease"),
    ],
)
def test_curated_pgp_rule_covers_matching_public_exposure_summary(
    names: list[str], rule_id: str, direction: str
) -> None:
    result = analyze_names(names, as_json_payload=True)
    assert result.ok
    assert rule_id in {
        hit["rule_id"]
        for report in result.payload["pairs"]
        for hit in report["pk"]["hits"]
    }
    assert not any(
        item["source"] == RESULT_SOURCE_AGGREGATE
        and f"exposure {direction}" in item["title"]
        for item in result.payload["public_result_summaries"]
    )
    assert result.payload["mechanism_pipeline"]["candidates"]


def test_pgp_rule_requires_explicit_family_and_correct_direction() -> None:
    pipeline = pipeline_for(["digoxin", "clarithromycin"])
    hit = RuleHit(
        rule_id="PK_PGP_INHIB_DIGOXIN",
        name="P-gp inhibition",
        domain=Domain.PK,
        severity=Severity.major,
        rule_class=RuleClass.caution,
        inputs={"A": "digoxin", "B": "clarithromycin", "transporter_family": "ABCB1"},
    )
    report = PairReport(
        drug_1="clarithromycin",
        drug_2="digoxin",
        overall_severity=Severity.major,
        overall_rule_class="caution",
        pk_hits=[hit],
    )
    assert [
        item.source for item in build_public_result_summaries(pipeline, [report])
    ] == [RESULT_SOURCE_RULE]
    for inputs, rule_id in (
        ({"A": "digoxin", "B": "clarithromycin"}, "PK_PGP_INHIB_DIGOXIN"),
        (
            {"A": "digoxin", "B": "clarithromycin", "transporter_family": "ABCG2"},
            "PK_PGP_INHIB_DIGOXIN",
        ),
        (
            {
                "A": "digoxin",
                "B": "clarithromycin",
                "transporter_family": "ABCB1",
                "transporter_id": "BCRP",
            },
            "PK_PGP_INHIB_DIGOXIN",
        ),
        (
            {"A": "digoxin", "B": "clarithromycin", "transporter_family": "ABCB1"},
            "PK_PGP_INDUC_DIGOXIN",
        ),
    ):
        wrong_hit = replace(hit, rule_id=rule_id, inputs=inputs)
        summaries = build_public_result_summaries(
            pipeline, [replace(report, pk_hits=[wrong_hit])]
        )
        assert {item.source for item in summaries} == {
            RESULT_SOURCE_AGGREGATE,
            RESULT_SOURCE_RULE,
        }
