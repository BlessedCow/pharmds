from core.mechanisms.aggregate_evidence import (
    EVIDENCE_STATUS_COMPLETE,
    EVIDENCE_STATUS_CONFLICTING,
    EVIDENCE_STATUS_DISPUTED,
    EVIDENCE_STATUS_MISSING,
    EVIDENCE_STATUS_NOT_APPLICABLE,
    EVIDENCE_STATUS_PARTIAL,
    AggregateEvidenceSummary,
    aggregate_to_evidence_summary,
    dedupe_aggregate_evidence_summaries,
    summarize_aggregate_evidence,
)
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AggregateConcern,
)
from core.mechanisms.policy import (
    POLICY_MECHANISTIC_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    ConcernPolicyResult,
)


def _pd_member(
    precipitant_drug: str,
    object_drug: str,
    *,
    evidence_trace,
) -> ConcernPolicyResult:
    return ConcernPolicyResult(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern="additive_pd_effect",
        precipitant_drug=precipitant_drug,
        object_drug=object_drug,
        effect_id="nausea",
        metadata={"evidence_trace": evidence_trace},
    )


def _trace(status: str) -> dict:
    return {
        "trace_type": "additive_pd_effect",
        "effect_id": "nausea",
        "drug_ids": ["clarithromycin", "fluconazole"],
        "overall_evidence_status": status,
        "drugs": [
            {
                "drug_id": "clarithromycin",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": (
                            "claim_clarithromycin_pd_effect_nausea_001"
                        ),
                        "evidence": [
                            {
                                "source_id": "source_clarithromycin_label",
                            }
                        ],
                    }
                ],
            },
            {
                "drug_id": "fluconazole",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": "claim_fluconazole_pd_effect_nausea_001",
                        "evidence": [
                            {
                                "source_id": "source_fluconazole_label",
                            }
                        ],
                    }
                ],
            },
        ],
    }


def test_aggregate_to_evidence_summary_summarizes_complete_trace():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
        members=(
            _pd_member(
                "clarithromycin",
                "fluconazole",
                evidence_trace=_trace(EVIDENCE_STATUS_COMPLETE),
            ),
        ),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.aggregate == aggregate
    assert summary.overall_evidence_status == EVIDENCE_STATUS_COMPLETE
    assert summary.evidence_trace_count == 1
    assert summary.evidence_trace_types == ("additive_pd_effect",)
    assert summary.evidence_effect_ids == ("nausea",)
    assert summary.evidence_statuses == (EVIDENCE_STATUS_COMPLETE,)
    assert summary.evidence_gap_count == 0
    assert summary.evidence_claim_count == 2
    assert summary.evidence_source_ids == (
        "source_clarithromycin_label",
        "source_fluconazole_label",
    )
    assert summary.member_without_evidence_trace_count == 0


def test_aggregate_to_evidence_summary_extracts_nested_source_ids():
    trace = _trace(EVIDENCE_STATUS_COMPLETE)
    trace["drugs"][0]["claims"][0]["evidence"] = [
        {
            "source": {
                "source_id": "source_nested_clarithromycin_label",
                "title": "Clarithromycin Prescribing Information",
                "source_type": "drug_label",
            },
        }
    ]

    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
        members=(
            _pd_member(
                "clarithromycin",
                "fluconazole",
                evidence_trace=trace,
            ),
        ),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.evidence_source_ids == (
        "source_fluconazole_label",
        "source_nested_clarithromycin_label",
    )

def test_aggregate_to_evidence_summary_counts_partial_evidence_gap():
    trace = _trace(EVIDENCE_STATUS_PARTIAL)
    trace["drugs"][1]["evidence_status"] = "missing"
    trace["drugs"][1]["claims"] = []

    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "alprazolam"),
        effect_id="nausea",
        members=(
            _pd_member(
                "alprazolam",
                "clarithromycin",
                evidence_trace=trace,
            ),
        ),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.overall_evidence_status == EVIDENCE_STATUS_PARTIAL
    assert summary.evidence_gap_count == 1
    assert summary.evidence_claim_count == 1
    assert summary.evidence_source_ids == ("source_clarithromycin_label",)


def test_aggregate_without_evidence_trace_is_not_applicable():
    member = ConcernPolicyResult(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern="exposure_increase",
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
    )
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        anchor="vortioxetine",
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        drugs=("bupropion", "vortioxetine"),
        targets=("CYP2D6",),
        members=(member,),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.overall_evidence_status == EVIDENCE_STATUS_NOT_APPLICABLE
    assert summary.evidence_trace_count == 0
    assert summary.evidence_gap_count == 0
    assert summary.evidence_claim_count == 0
    assert summary.member_without_evidence_trace_count == 1


def test_summarize_aggregate_evidence_preserves_order():
    aggregate_a = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("a", "b"),
        effect_id="nausea",
    )
    aggregate_b = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="sedation",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("a", "b"),
        effect_id="sedation",
    )

    summaries = summarize_aggregate_evidence([aggregate_a, aggregate_b])

    assert [summary.aggregate for summary in summaries] == [
        aggregate_a,
        aggregate_b,
    ]


def test_dedupe_aggregate_evidence_summaries_preserves_first_seen():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("a", "b"),
        effect_id="nausea",
    )
    first = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_COMPLETE,
    )
    second = AggregateEvidenceSummary(
        aggregate=aggregate,
        overall_evidence_status=EVIDENCE_STATUS_PARTIAL,
    )

    assert dedupe_aggregate_evidence_summaries([first, second]) == [first]
    
def test_aggregate_evidence_conflicting_status_overrides_complete():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
        members=(
            _pd_member(
                "clarithromycin",
                "fluconazole",
                evidence_trace=_trace(EVIDENCE_STATUS_COMPLETE),
            ),
            _pd_member(
                "fluconazole",
                "clarithromycin",
                evidence_trace=_trace(EVIDENCE_STATUS_CONFLICTING),
            ),
        ),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.overall_evidence_status == EVIDENCE_STATUS_CONFLICTING
    assert summary.evidence_statuses == (
        EVIDENCE_STATUS_COMPLETE,
        EVIDENCE_STATUS_CONFLICTING,
    )


def test_aggregate_evidence_partial_status_overrides_disputed():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
        members=(
            _pd_member(
                "clarithromycin",
                "fluconazole",
                evidence_trace=_trace(EVIDENCE_STATUS_DISPUTED),
            ),
            _pd_member(
                "fluconazole",
                "clarithromycin",
                evidence_trace=_trace(EVIDENCE_STATUS_PARTIAL),
            ),
        ),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.overall_evidence_status == EVIDENCE_STATUS_PARTIAL
    assert summary.evidence_statuses == (
        EVIDENCE_STATUS_DISPUTED,
        EVIDENCE_STATUS_PARTIAL,
    )


def test_aggregate_evidence_missing_status_is_not_complete():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
        members=(
            _pd_member(
                "clarithromycin",
                "fluconazole",
                evidence_trace=_trace(EVIDENCE_STATUS_MISSING),
            ),
        ),
    )

    summary = aggregate_to_evidence_summary(aggregate)

    assert summary.overall_evidence_status == EVIDENCE_STATUS_MISSING
    assert summary.evidence_statuses == (EVIDENCE_STATUS_MISSING,)