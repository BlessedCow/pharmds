from core.mechanisms.aggregate_evidence import (
    EVIDENCE_STATUS_COMPLETE,
    AggregateEvidenceSummary,
)
from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
from core.mechanisms.aggregate_summary import (
    AggregateConcernSummary,
    build_aggregate_concern_summaries,
    dedupe_aggregate_concern_summaries,
)
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AggregateConcern,
)
from core.mechanisms.policy import (
    POLICY_MECHANISTIC_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
)


def _pd_aggregate() -> AggregateConcern:
    return AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
    )


def _pk_aggregate() -> AggregateConcern:
    return AggregateConcern(
        aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        anchor="vortioxetine",
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        drugs=("bupropion", "vortioxetine"),
        targets=("CYP2D6",),
    )


def test_build_aggregate_concern_summaries_joins_matching_layers():
    aggregate = _pd_aggregate()
    severity = AggregateSeverityAnnotation(
        aggregate=aggregate,
        strongest_preliminary_severity="caution",
        contributing_preliminary_severities=("caution",),
        severity_reasons=("Multiple tolerability-related candidates identified.",),
    )
    evidence = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_COMPLETE,
        evidence_trace_count=1,
        evidence_effect_ids=("nausea",),
        evidence_gap_count=0,
        evidence_claim_count=2,
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [severity],
        [evidence],
    )

    assert summaries == [
        AggregateConcernSummary(
            aggregate=aggregate,
            severity_annotation=severity,
            evidence_summary=evidence,
        )
    ]


def test_build_aggregate_concern_summaries_handles_missing_severity():
    aggregate = _pd_aggregate()
    evidence = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_COMPLETE,
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [evidence],
    )

    assert len(summaries) == 1
    assert summaries[0].aggregate == aggregate
    assert summaries[0].severity_annotation is None
    assert summaries[0].evidence_summary == evidence


def test_build_aggregate_concern_summaries_handles_missing_evidence():
    aggregate = _pk_aggregate()
    severity = AggregateSeverityAnnotation(
        aggregate=aggregate,
        strongest_preliminary_severity="informational",
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [severity],
        [],
    )

    assert len(summaries) == 1
    assert summaries[0].aggregate == aggregate
    assert summaries[0].severity_annotation == severity
    assert summaries[0].evidence_summary is None


def test_build_aggregate_concern_summaries_preserves_aggregate_order():
    aggregate_a = _pd_aggregate()
    aggregate_b = _pk_aggregate()

    summaries = build_aggregate_concern_summaries(
        [aggregate_a, aggregate_b],
        [],
        [],
    )

    assert [summary.aggregate for summary in summaries] == [
        aggregate_a,
        aggregate_b,
    ]


def test_dedupe_aggregate_concern_summaries_preserves_first_seen():
    aggregate = _pd_aggregate()
    first = AggregateConcernSummary(
        aggregate=aggregate,
        severity_annotation=AggregateSeverityAnnotation(
            aggregate=aggregate,
            strongest_preliminary_severity="informational",
        ),
    )
    second = AggregateConcernSummary(
        aggregate=aggregate,
        severity_annotation=AggregateSeverityAnnotation(
            aggregate=aggregate,
            strongest_preliminary_severity="caution",
        ),
    )

    assert dedupe_aggregate_concern_summaries([first, second]) == [first]