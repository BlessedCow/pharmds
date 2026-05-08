from core.mechanisms.arbitration import (
    CONCERN_ADDITIVE_PD_EFFECT,
    CONCERN_EXPOSURE_DECREASE,
    CONCERN_EXPOSURE_INCREASE,
)
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanisms.policy import (
    POLICY_EXPOSURE_REDUCTION_CONCERN,
    POLICY_MECHANISTIC_CONCERN,
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
    POLICY_UNKNOWN_CONCERN,
)
from core.mechanisms.scoring import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MODERATE,
    SEVERITY_UNSCORED,
    ScoredConcern,
)
from core.mechanisms.severity import (
    PRELIMINARY_SEVERITY_CAUTION,
    PRELIMINARY_SEVERITY_HIGH_CAUTION,
    PRELIMINARY_SEVERITY_INFORMATIONAL,
    PRELIMINARY_SEVERITY_UNSCORED,
    SeverityAnnotatedConcern,
    annotate_preliminary_severity,
    dedupe_severity_annotations,
    scored_concern_to_severity_annotation,
)


def test_high_confidence_safety_concern_maps_to_high_caution():
    concern = ScoredConcern(
        policy_concern=POLICY_SAFETY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="clarithromycin",
        object_drug="fluconazole",
        effect_id="QT_prolongation",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        confidence=CONFIDENCE_HIGH,
        severity=SEVERITY_UNSCORED,
    )

    annotated = scored_concern_to_severity_annotation(concern)

    assert annotated.scored == concern
    assert annotated.preliminary_severity == PRELIMINARY_SEVERITY_HIGH_CAUTION
    assert annotated.severity_reason == "High-confidence safety concern."


def test_multi_mechanism_exposure_increase_maps_to_caution():
    concern = ScoredConcern(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        confidence=CONFIDENCE_HIGH,
        severity=SEVERITY_UNSCORED,
        aggregate_member_count=3,
        related_targets=("CYP2C19", "CYP2C9", "CYP2D6"),
    )

    annotated = scored_concern_to_severity_annotation(concern)

    assert annotated.preliminary_severity == PRELIMINARY_SEVERITY_CAUTION
    assert annotated.severity_reason == (
        "Multiple mechanism candidates affect the same object drug."
    )


def test_single_high_confidence_mechanistic_concern_maps_to_informational():
    concern = ScoredConcern(
        policy_concern=POLICY_MECHANISTIC_CONCERN,
        source_concern=CONCERN_EXPOSURE_INCREASE,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        confidence=CONFIDENCE_HIGH,
        severity=SEVERITY_UNSCORED,
        aggregate_member_count=1,
        related_targets=("CYP2D6",),
    )

    annotated = scored_concern_to_severity_annotation(concern)

    assert annotated.preliminary_severity == PRELIMINARY_SEVERITY_INFORMATIONAL
    assert annotated.severity_reason == (
        "Single high-confidence mechanistic concern."
    )


def test_exposure_reduction_concern_maps_to_informational():
    concern = ScoredConcern(
        policy_concern=POLICY_EXPOSURE_REDUCTION_CONCERN,
        source_concern=CONCERN_EXPOSURE_DECREASE,
        precipitant_drug="rifampin",
        object_drug="vortioxetine",
        target="CYP3A4",
        candidate_type=CANDIDATE_ENZYME_INDUCTION,
        confidence=CONFIDENCE_HIGH,
        severity=SEVERITY_UNSCORED,
    )

    annotated = scored_concern_to_severity_annotation(concern)

    assert annotated.preliminary_severity == PRELIMINARY_SEVERITY_INFORMATIONAL
    assert annotated.severity_reason == "Exposure-reduction concern identified."


def test_tolerability_concern_maps_to_informational():
    concern = ScoredConcern(
        policy_concern=POLICY_TOLERABILITY_CONCERN,
        source_concern=CONCERN_ADDITIVE_PD_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        confidence=CONFIDENCE_MODERATE,
        severity=SEVERITY_UNSCORED,
        aggregate_member_count=1,
        related_effects=("nausea",),
    )

    annotated = scored_concern_to_severity_annotation(concern)

    assert annotated.preliminary_severity == PRELIMINARY_SEVERITY_INFORMATIONAL
    assert annotated.severity_reason == "Tolerability concern identified."


def test_low_confidence_unknown_concern_remains_unscored():
    concern = ScoredConcern(
        policy_concern=POLICY_UNKNOWN_CONCERN,
        source_concern="unknown",
        precipitant_drug="drug_a",
        object_drug="drug_b",
        effect_id="uncategorized_effect",
        candidate_type="UNKNOWN_CANDIDATE",
        confidence=CONFIDENCE_LOW,
        severity=SEVERITY_UNSCORED,
    )

    annotated = scored_concern_to_severity_annotation(concern)

    assert annotated.preliminary_severity == PRELIMINARY_SEVERITY_UNSCORED
    assert annotated.severity_reason == (
        "Insufficient confidence for preliminary severity annotation."
    )


def test_annotate_preliminary_severity_maps_multiple_concerns():
    concerns = [
        ScoredConcern(
            policy_concern=POLICY_MECHANISTIC_CONCERN,
            source_concern=CONCERN_EXPOSURE_INCREASE,
            precipitant_drug="bupropion",
            object_drug="vortioxetine",
            target="CYP2D6",
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
            confidence=CONFIDENCE_HIGH,
            severity=SEVERITY_UNSCORED,
        ),
        ScoredConcern(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            confidence=CONFIDENCE_MODERATE,
            severity=SEVERITY_UNSCORED,
        ),
    ]

    annotated = annotate_preliminary_severity(concerns)

    assert len(annotated) == 2
    assert annotated[0].preliminary_severity == (
        PRELIMINARY_SEVERITY_INFORMATIONAL
    )
    assert annotated[1].preliminary_severity == (
        PRELIMINARY_SEVERITY_INFORMATIONAL
    )


def test_dedupe_severity_annotations_preserves_first_seen_order():
    first = SeverityAnnotatedConcern(
        scored=ScoredConcern(
            policy_concern=POLICY_TOLERABILITY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            confidence=CONFIDENCE_MODERATE,
        ),
        preliminary_severity=PRELIMINARY_SEVERITY_INFORMATIONAL,
    )
    duplicate = SeverityAnnotatedConcern(
        scored=first.scored,
        preliminary_severity=PRELIMINARY_SEVERITY_INFORMATIONAL,
    )
    second = SeverityAnnotatedConcern(
        scored=ScoredConcern(
            policy_concern=POLICY_SAFETY_CONCERN,
            source_concern=CONCERN_ADDITIVE_PD_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="fluconazole",
            effect_id="QT_prolongation",
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            confidence=CONFIDENCE_HIGH,
        ),
        preliminary_severity=PRELIMINARY_SEVERITY_HIGH_CAUTION,
    )

    deduped = dedupe_severity_annotations([first, duplicate, second])

    assert len(deduped) == 2
    assert deduped[0].scored.effect_id == "nausea"
    assert deduped[1].scored.effect_id == "QT_prolongation"