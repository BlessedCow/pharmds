from core.enums import Domain, RuleClass, Severity
from core.mechanisms.aggregate_evidence import AggregateEvidenceSummary
from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
from core.mechanisms.aggregate_summary import (
    build_aggregate_concern_summaries,
)
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AggregateConcern,
)
from core.mechanisms.pipeline import MechanismPipelineResult
from core.mechanisms.result_summary import (
    RESULT_SOURCE_AGGREGATE,
    RESULT_SOURCE_RULE,
    aggregate_summary_to_result_summary,
    build_public_result_summaries,
    legacy_rule_hit_to_result_summary,
    result_summaries_to_json_dicts,
    result_summary_to_json_dict,
)
from core.models import PairReport, RuleHit


def _empty_pipeline(
    aggregate_concern_summaries=(),
):
    return MechanismPipelineResult(
        effects=(),
        candidates=(),
        arbitration_results=(),
        policy_results=(),
        scored_concerns=(),
        severity_annotations=(),
        aggregate_concerns=(),
        aggregate_severity_annotations=(),
        aggregate_evidence_summaries=(),
        aggregate_concern_summaries=tuple(aggregate_concern_summaries),
    )


def test_aggregate_summary_to_result_summary_uses_public_shape():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern="tolerability_concern",
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
    )
    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [
            AggregateSeverityAnnotation(
                aggregate=aggregate,
                strongest_preliminary_severity="informational",
            )
        ],
        [
            AggregateEvidenceSummary(
                aggregate=aggregate,
                overall_evidence_status="complete",
            )
        ],
    )

    result = aggregate_summary_to_result_summary(summaries[0])

    assert result.source == RESULT_SOURCE_AGGREGATE
    assert result.title == "Shared nausea concern"
    assert result.drugs == ("clarithromycin", "fluconazole")
    assert result.concern_type == "tolerability_concern"
    assert result.severity_label == "informational"
    assert result.evidence_label == "complete"
    assert "nausea-related pharmacodynamic effect" in result.explanation
    assert "educational and not diagnostic" in result.explanation


def test_aggregate_exposure_summary_to_result_summary_uses_public_title():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        anchor="vortioxetine",
        policy_concern="mechanistic_concern",
        drugs=("bupropion", "vortioxetine"),
        targets=("CYP2D6",),
    )
    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [
            AggregateSeverityAnnotation(
                aggregate=aggregate,
                strongest_preliminary_severity="informational",
            )
        ],
        [
            AggregateEvidenceSummary(
                aggregate=aggregate,
                overall_evidence_status="not_applicable",
            )
        ],
    )

    result = aggregate_summary_to_result_summary(summaries[0])

    assert result.title == "vortioxetine exposure increase concern"
    assert result.drugs == ("bupropion", "vortioxetine")
    assert result.concern_type == "mechanistic_concern"
    assert result.severity_label == "informational"
    assert result.evidence_label == "not_applicable"
    assert "vortioxetine exposure" in result.explanation


def test_legacy_rule_hit_to_result_summary_uses_public_shape():
    hit = RuleHit(
        rule_id="pd_test_rule",
        name="Additive CNS depression",
        domain=Domain.PD,
        severity=Severity.caution,
        rule_class=RuleClass.caution,
        inputs={
            "A": "alcohol",
            "B": "clonazepam",
        },
        rationale=[
            "Both selected drugs may contribute to CNS depression.",
        ],
    )
    report = PairReport(
        drug_1="alcohol",
        drug_2="clonazepam",
        overall_severity=Severity.caution,
        overall_rule_class="caution",
        pd_hits=[hit],
    )

    result = legacy_rule_hit_to_result_summary(report, hit)

    assert result.source == RESULT_SOURCE_RULE
    assert result.title == "Additive CNS depression"
    assert result.drugs == ("alcohol", "clonazepam")
    assert result.concern_type == "PD"
    assert result.severity_label == "caution"
    assert result.evidence_label == "legacy_rule"
    assert result.explanation == (
        "Both selected drugs may contribute to CNS depression."
    )


def test_build_public_result_summaries_combines_aggregate_and_legacy_rules():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="sedation",
        policy_concern="tolerability_concern",
        drugs=("alcohol", "clonazepam"),
        effect_id="sedation",
    )
    aggregate_summaries = build_aggregate_concern_summaries(
        [aggregate],
        [
            AggregateSeverityAnnotation(
                aggregate=aggregate,
                strongest_preliminary_severity="caution",
            )
        ],
        [
            AggregateEvidenceSummary(
                aggregate=aggregate,
                overall_evidence_status="complete",
            )
        ],
    )
    pipeline = _empty_pipeline(
        aggregate_concern_summaries=aggregate_summaries,
    )

    hit = RuleHit(
        rule_id="pd_test_rule",
        name="Additive CNS depression",
        domain=Domain.PD,
        severity=Severity.caution,
        rule_class=RuleClass.caution,
        inputs={
            "A": "alcohol",
            "B": "clonazepam",
        },
        rationale=[
            "Both selected drugs may contribute to CNS depression.",
        ],
    )
    pair_reports = [
        PairReport(
            drug_1="alcohol",
            drug_2="clonazepam",
            overall_severity=Severity.caution,
            overall_rule_class="caution",
            pd_hits=[hit],
        )
    ]

    results = build_public_result_summaries(
        pipeline,
        pair_reports=pair_reports,
    )

    assert [result.source for result in results] == [
        RESULT_SOURCE_AGGREGATE,
        RESULT_SOURCE_RULE,
    ]
    assert results[0].title == "Shared sedation concern"
    assert results[1].title == "Additive CNS depression"


def test_result_summary_json_does_not_expose_internal_debug_fields():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern="tolerability_concern",
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
    )
    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [
            AggregateSeverityAnnotation(
                aggregate=aggregate,
                strongest_preliminary_severity="informational",
            )
        ],
        [
            AggregateEvidenceSummary(
                aggregate=aggregate,
                overall_evidence_status="complete",
            )
        ],
    )
    result = aggregate_summary_to_result_summary(summaries[0])

    payload = result_summary_to_json_dict(result)

    assert set(payload) == {
        "source",
        "title",
        "drugs",
        "concern_type",
        "severity_label",
        "evidence_label",
        "explanation",
    }

    assert "aggregate" not in payload
    assert "members" not in payload
    assert "severity_annotation" not in payload
    assert "evidence_summary" not in payload
    assert "evidence_conflict_source_ids" not in payload
    assert "evidence_conflict_trace_types" not in payload


def test_result_summaries_to_json_dicts_returns_public_list():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern="tolerability_concern",
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
    )
    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [],
    )
    result = aggregate_summary_to_result_summary(summaries[0])

    payload = result_summaries_to_json_dicts([result])

    assert payload == [
        result_summary_to_json_dict(result),
    ]