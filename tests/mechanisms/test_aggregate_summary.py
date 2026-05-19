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
    
    
def test_build_aggregate_concern_summaries_ranks_by_severity_first():
    lower = _pd_aggregate()
    higher = _pk_aggregate()

    summaries = build_aggregate_concern_summaries(
        [lower, higher],
        [
            AggregateSeverityAnnotation(
                aggregate=lower,
                strongest_preliminary_severity="informational",
            ),
            AggregateSeverityAnnotation(
                aggregate=higher,
                strongest_preliminary_severity="caution",
            ),
        ],
        [],
    )

    assert [summary.aggregate for summary in summaries] == [higher, lower]

def test_build_aggregate_concern_summaries_ranks_evidence_when_severity_ties():
    partial = _pd_aggregate()
    complete = _pk_aggregate()

    summaries = build_aggregate_concern_summaries(
        [partial, complete],
        [
            AggregateSeverityAnnotation(
                aggregate=partial,
                strongest_preliminary_severity="caution",
            ),
            AggregateSeverityAnnotation(
                aggregate=complete,
                strongest_preliminary_severity="caution",
            ),
        ],
        [
            AggregateEvidenceSummary(
                aggregate=partial,
                overall_evidence_status="partial",
            ),
            AggregateEvidenceSummary(
                aggregate=complete,
                overall_evidence_status="complete",
            ),
        ],
    )

    assert [summary.aggregate for summary in summaries] == [complete, partial]


def test_build_aggregate_concern_summaries_keeps_stable_order_on_rank_tie():
    first = _pd_aggregate()
    second = _pk_aggregate()

    summaries = build_aggregate_concern_summaries(
        [first, second],
        [
            AggregateSeverityAnnotation(
                aggregate=first,
                strongest_preliminary_severity="caution",
            ),
            AggregateSeverityAnnotation(
                aggregate=second,
                strongest_preliminary_severity="caution",
            ),
        ],
        [
            AggregateEvidenceSummary(
                aggregate=first,
                overall_evidence_status="complete",
            ),
            AggregateEvidenceSummary(
                aggregate=second,
                overall_evidence_status="complete",
            ),
        ],
    )

    assert [summary.aggregate for summary in summaries] == [first, second]
    
def test_build_aggregate_concern_summaries_adds_qt_risk_modifier():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="QT_prolongation",
        policy_concern="safety_concern",
        drugs=("clarithromycin", "fluconazole"),
        effect_id="QT_prolongation",
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [],
        patient_flags={
            "qt_risk": True,
            "bleeding_risk": False,
        },
    )

    assert summaries[0].patient_risk_modifiers == ("qt_risk",)
    assert summaries[0].risk_context == (
        "QT-related concern may be more important when QT risk flag is present."
    )


def test_build_aggregate_concern_summaries_adds_bleeding_risk_modifier():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="bleeding",
        policy_concern="safety_concern",
        drugs=("ibuprofen", "warfarin"),
        effect_id="bleeding",
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [],
        patient_flags={
            "qt_risk": False,
            "bleeding_risk": True,
        },
    )

    assert summaries[0].patient_risk_modifiers == ("bleeding_risk",)
    assert summaries[0].risk_context == (
        "Bleeding-related concern may be more important when bleeding risk flag "
        "is present."
    )


def test_build_aggregate_concern_summaries_ignores_irrelevant_patient_flag():
    aggregate = _pd_aggregate()

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [],
        patient_flags={
            "qt_risk": True,
            "bleeding_risk": True,
        },
    )

    assert summaries[0].patient_risk_modifiers == ()
    assert summaries[0].risk_context is None