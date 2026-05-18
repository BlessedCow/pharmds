from core.mechanisms.aggregate_severity import (
    AggregateSeverityAnnotation,
    aggregate_to_severity_annotation,
    annotate_aggregate_preliminary_severity,
    dedupe_aggregate_severity_annotations,
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
from core.mechanisms.scoring import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MODERATE,
    ScoredConcern,
)
from core.mechanisms.severity import (
    PRELIMINARY_SEVERITY_CAUTION,
    PRELIMINARY_SEVERITY_HIGH_CAUTION,
    PRELIMINARY_SEVERITY_INFORMATIONAL,
    SeverityAnnotatedConcern,
)


def test_aggregate_to_severity_annotation_summarizes_member_severities():
    member_a = ConcernPolicyResult(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern="additive_pd_effect",
        precipitant_drug="clarithromycin",
        object_drug="fluconazole",
        effect_id="nausea",
    )
    member_b = ConcernPolicyResult(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern="additive_pd_effect",
        precipitant_drug="fluconazole",
        object_drug="clarithromycin",
        effect_id="nausea",
    )
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("clarithromycin", "fluconazole"),
        effect_id="nausea",
        members=(member_a, member_b),
    )
    annotations = [
        SeverityAnnotatedConcern(
            scored=ScoredConcern(
                policy_concern=member_a.policy_concern,
                source_concern=member_a.source_concern,
                precipitant_drug=member_a.precipitant_drug,
                object_drug=member_a.object_drug,
                effect_id=member_a.effect_id,
                confidence=CONFIDENCE_MODERATE,
            ),
            preliminary_severity=PRELIMINARY_SEVERITY_INFORMATIONAL,
            severity_reason="Tolerability concern identified.",
        ),
        SeverityAnnotatedConcern(
            scored=ScoredConcern(
                policy_concern=member_b.policy_concern,
                source_concern=member_b.source_concern,
                precipitant_drug=member_b.precipitant_drug,
                object_drug=member_b.object_drug,
                effect_id=member_b.effect_id,
                confidence=CONFIDENCE_HIGH,
            ),
            preliminary_severity=PRELIMINARY_SEVERITY_CAUTION,
            severity_reason="Multiple tolerability-related candidates identified.",
        ),
    ]

    annotation = aggregate_to_severity_annotation(aggregate, annotations)

    assert annotation.aggregate == aggregate
    assert annotation.strongest_preliminary_severity == PRELIMINARY_SEVERITY_CAUTION
    assert annotation.contributing_preliminary_severities == (
        PRELIMINARY_SEVERITY_CAUTION,
        PRELIMINARY_SEVERITY_INFORMATIONAL,
    )
    assert annotation.severity_reasons == (
        "Multiple tolerability-related candidates identified.",
        "Tolerability concern identified.",
    )


def test_aggregate_to_severity_annotation_uses_member_keys_not_only_effect_id():
    included_member = ConcernPolicyResult(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern="exposure_increase",
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
    )
    excluded_member = ConcernPolicyResult(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern="exposure_increase",
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        target="CYP3A4",
    )
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        anchor="vortioxetine",
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        drugs=("bupropion", "vortioxetine"),
        targets=("CYP2D6",),
        members=(included_member,),
    )
    annotations = [
        SeverityAnnotatedConcern(
            scored=ScoredConcern(
                policy_concern=included_member.policy_concern,
                source_concern=included_member.source_concern,
                precipitant_drug=included_member.precipitant_drug,
                object_drug=included_member.object_drug,
                target=included_member.target,
            ),
            preliminary_severity=PRELIMINARY_SEVERITY_INFORMATIONAL,
            severity_reason="Included.",
        ),
        SeverityAnnotatedConcern(
            scored=ScoredConcern(
                policy_concern=excluded_member.policy_concern,
                source_concern=excluded_member.source_concern,
                precipitant_drug=excluded_member.precipitant_drug,
                object_drug=excluded_member.object_drug,
                target=excluded_member.target,
            ),
            preliminary_severity=PRELIMINARY_SEVERITY_HIGH_CAUTION,
            severity_reason="Excluded.",
        ),
    ]

    annotation = aggregate_to_severity_annotation(aggregate, annotations)

    assert (
        annotation.strongest_preliminary_severity
        == PRELIMINARY_SEVERITY_INFORMATIONAL
    )
    assert annotation.severity_reasons == ("Included.",)


def test_annotate_aggregate_preliminary_severity_preserves_order():
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

    annotations = annotate_aggregate_preliminary_severity(
        [aggregate_a, aggregate_b],
        [],
    )

    assert [item.aggregate for item in annotations] == [aggregate_a, aggregate_b]


def test_dedupe_aggregate_severity_annotations_preserves_first_seen():
    aggregate = AggregateConcern(
        aggregate_type=AGGREGATE_SHARED_PD_EFFECT,
        anchor="nausea",
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        drugs=("a", "b"),
        effect_id="nausea",
    )
    first = AggregateSeverityAnnotation(
        aggregate=aggregate,
        strongest_preliminary_severity=PRELIMINARY_SEVERITY_INFORMATIONAL,
    )
    second = AggregateSeverityAnnotation(
        aggregate=aggregate,
        strongest_preliminary_severity=PRELIMINARY_SEVERITY_CAUTION,
    )

    assert dedupe_aggregate_severity_annotations([first, second]) == [first]