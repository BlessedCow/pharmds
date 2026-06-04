from core.mechanisms.aggregate_evidence import (
    EVIDENCE_STATUS_COMPLETE,
    EVIDENCE_STATUS_CONFLICTING,
    EVIDENCE_STATUS_DISPUTED,
    EVIDENCE_STATUS_MISSING,
    EVIDENCE_STATUS_NOT_APPLICABLE,
    EVIDENCE_STATUS_PARTIAL,
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

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.aggregate == aggregate
    assert summary.severity_annotation == severity
    assert summary.evidence_summary == evidence
    assert summary.patient_risk_modifiers == ()
    assert summary.risk_context is None
    assert summary.narrative
    assert (
        "clarithromycin and fluconazole share a regimen-wide nausea-related "
        "pharmacodynamic concern."
    ) in (        summary.narrative
    )
    assert "complete curated evidence support" in summary.narrative
    assert "preliminary educational severity label is caution" in summary.narrative
    assert "educational and not diagnostic" in summary.narrative


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
    
def test_build_aggregate_concern_summaries_adds_pd_narrative():
    aggregate = _pd_aggregate()

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

    assert summaries[0].narrative == (
        "clarithromycin and fluconazole share a regimen-wide nausea-related "
        "pharmacodynamic concern. This grouped concern has complete curated "
        "evidence support. Its preliminary educational severity label is "
        "informational. This explanation is educational and not diagnostic."
    )


def test_build_aggregate_concern_summaries_adds_pk_narrative():
    aggregate = _pk_aggregate()

    summaries = build_aggregate_concern_summaries(
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
                overall_evidence_status="not_applicable",
            )
        ],
    )

    assert summaries[0].narrative == (
        "bupropion and vortioxetine include regimen-wide mechanism(s) that may "
        "increase vortioxetine exposure through CYP2D6-related mechanism(s). "
        "This grouped concern has no aggregate-level curated evidence "
        "requirement. Its preliminary educational severity label is caution. "
        "This explanation is educational and not diagnostic."
    )

def test_build_aggregate_concern_summaries_adds_patient_risk_to_narrative():
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

    assert (
        "Patient risk modifier(s) present: qt_risk. QT-related concern may "
        "be more important when QT risk flag is present."
    ) in summaries[0].narrative
    assert summaries[0].narrative.endswith(
        "This explanation is educational and not diagnostic."
    )
def test_build_aggregate_concern_summaries_surfaces_conflicting_evidence():
    aggregate = _pd_aggregate()
    evidence = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_CONFLICTING,
        evidence_trace_types=("additive_pd_effect",),
        evidence_source_ids=(
            "source_a",
            "source_b",
        ),
        evidence_conflict_reasons=(
            "claim_disagreement",
            "confidence",
        ),
    )
    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [evidence],
    )

    summary = summaries[0]

    assert summary.evidence_conflict_level == "conflicting"
    assert summary.evidence_conflict_message == (
        "Conflicting curated evidence is attached to this aggregate concern "
        "and should be reviewed separately instead of being treated as "
        "complete support. Conflict indicator(s): claim disagreement and "
        "confidence limitations."
    )
    assert summary.evidence_conflict_source_ids == ("source_a", "source_b")
    assert summary.evidence_conflict_trace_types == ("additive_pd_effect",)
    assert summary.evidence_conflict_reasons == (
        "claim_disagreement",
        "confidence",
    )
    assert "Conflicting curated evidence" in summary.narrative

def test_aggregate_summary_narrative_explains_partial_evidence_reason():
    aggregate = _pd_aggregate()
    evidence = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_PARTIAL,
        evidence_conflict_reasons=("coverage",),
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [evidence],
    )

    summary = summaries[0]

    assert summary.evidence_conflict_level == "none"
    assert summary.evidence_conflict_message is None
    assert summary.evidence_conflict_reasons == ("coverage",)
    assert (
        "Evidence limitation indicator(s): coverage gaps."
        in summary.narrative
    )

def test_build_aggregate_concern_summaries_surfaces_disputed_evidence():
    aggregate = _pd_aggregate()
    evidence = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_DISPUTED,
        evidence_trace_types=("additive_pd_effect",),
        evidence_source_ids=("source_a",),
        evidence_conflict_reasons=("source_mismatch",),
    )

    summaries = build_aggregate_concern_summaries(
        [aggregate],
        [],
        [evidence],
    )

    summary = summaries[0]

    assert summary.evidence_conflict_level == "disputed"
    assert summary.evidence_conflict_message == (
        "Disputed curated evidence is attached to this aggregate concern "
        "and should be reviewed separately. Dispute indicator(s): mixed "
        "source types."
    )
    assert summary.evidence_conflict_source_ids == ("source_a",)
    assert summary.evidence_conflict_trace_types == ("additive_pd_effect",)
    assert summary.evidence_conflict_reasons == ("source_mismatch",)
    assert "Disputed curated evidence" in summary.narrative


def test_build_aggregate_concern_summaries_does_not_flag_non_conflict_statuses():
    aggregate = _pd_aggregate()

    for status in (
        EVIDENCE_STATUS_COMPLETE,
        EVIDENCE_STATUS_PARTIAL,
        EVIDENCE_STATUS_MISSING,
        EVIDENCE_STATUS_NOT_APPLICABLE,
    ):
        evidence = AggregateEvidenceSummary(
            aggregate=aggregate,
            overall_evidence_status=status,
            evidence_trace_types=("additive_pd_effect",),
            evidence_source_ids=("source_a",),
        )

        summaries = build_aggregate_concern_summaries(
            [aggregate],
            [],
            [evidence],
        )

        summary = summaries[0]

        assert summary.evidence_conflict_level == "none"
        assert summary.evidence_conflict_message is None
        assert summary.evidence_conflict_source_ids == ()
        assert summary.evidence_conflict_trace_types == ()