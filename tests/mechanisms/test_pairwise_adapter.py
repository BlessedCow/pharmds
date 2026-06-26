from __future__ import annotations

from app.cli import DB_PATH, connect, load_facts, resolve_drug_ids
from app.service import analyze_names
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanisms.pairwise_adapter import (
    PAIRWISE_ADAPTER_DOMAIN_PD,
    PAIRWISE_ADAPTER_DOMAIN_PK,
    PairwiseMechanismConcern,
    adapt_mechanism_pipeline_to_pairwise,
)
from core.mechanisms.pipeline import run_mechanism_pipeline
from core.mechanisms.severity import (
    PRELIMINARY_SEVERITY_HIGH_CAUTION,
    PRELIMINARY_SEVERITY_INFORMATIONAL,
)


def _pipeline_for(drug_names: list[str]):
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
        facts = load_facts(conn, drug_ids, patient_flags={})
    finally:
        conn.close()

    return run_mechanism_pipeline(drug_ids, facts)


def _pairwise_concerns_for(
    drug_names: list[str],
) -> tuple[PairwiseMechanismConcern, ...]:
    return adapt_mechanism_pipeline_to_pairwise(_pipeline_for(drug_names))


def test_pairwise_adapter_shapes_pk_mechanism_concern() -> None:
    concerns = _pairwise_concerns_for(["clarithromycin", "midazolam"])

    assert len(concerns) == 1

    concern = concerns[0]

    assert concern.pair_key == ("clarithromycin", "midazolam")
    assert concern.precipitant_drug == "clarithromycin"
    assert concern.object_drug == "midazolam"
    assert concern.domain == PAIRWISE_ADAPTER_DOMAIN_PK
    assert concern.concern_id == "CYP3A4"
    assert concern.policy_concern == "mechanistic_concern"
    assert concern.source_concern == "exposure_increase"
    assert concern.severity == PRELIMINARY_SEVERITY_INFORMATIONAL
    assert concern.confidence == "unscored"
    assert concern.target == "CYP3A4"
    assert concern.effect_id is None
    assert concern.candidate_type == CANDIDATE_ENZYME_INHIBITION
    assert "clarithromycin" in concern.explanation
    assert "CYP3A4" in concern.explanation
    assert "midazolam" in concern.explanation
    assert concern.explanation_fields == {
        "precipitant_drug": "clarithromycin",
        "object_drug": "midazolam",
        "target": "CYP3A4",
        "effect_id": None,
        "candidate_type": CANDIDATE_ENZYME_INHIBITION,
        "aggregate_types": ("object_exposure_increase_cluster",),
        "aggregate_targets": ("CYP3A4",),
        "aggregate_effects": (),
    }


def test_pairwise_adapter_shapes_pd_safety_concern() -> None:
    concerns = _pairwise_concerns_for(["clarithromycin", "ondansetron"])

    qt_concern = next(
        concern
        for concern in concerns
        if concern.concern_id == "QT_prolongation"
    )

    assert qt_concern.pair_key == ("clarithromycin", "ondansetron")
    assert qt_concern.domain == PAIRWISE_ADAPTER_DOMAIN_PD
    assert qt_concern.policy_concern == "safety_concern"
    assert qt_concern.source_concern == "additive_pd_effect"
    assert qt_concern.severity == PRELIMINARY_SEVERITY_HIGH_CAUTION
    assert qt_concern.effect_id == "QT_prolongation"
    assert qt_concern.target is None
    assert qt_concern.explanation_fields == {
        "precipitant_drug": "clarithromycin",
        "object_drug": "ondansetron",
        "target": None,
        "effect_id": "QT_prolongation",
        "candidate_type": CANDIDATE_PD_SHARED_EFFECT,
        "aggregate_types": (
            "safety_concern_cluster",
            "shared_pd_effect_cluster",
        ),
        "aggregate_targets": (),
        "aggregate_effects": ("QT_prolongation",),
    }


def test_pairwise_adapter_preserves_directional_pair_identity() -> None:
    concerns = _pairwise_concerns_for(["bupropion", "vortioxetine"])

    cyp2d6_concern = next(
        concern
        for concern in concerns
        if concern.concern_id == "CYP2D6"
    )

    assert cyp2d6_concern.pair_key == ("bupropion", "vortioxetine")
    assert cyp2d6_concern.precipitant_drug == "bupropion"
    assert cyp2d6_concern.object_drug == "vortioxetine"
    assert cyp2d6_concern.domain == PAIRWISE_ADAPTER_DOMAIN_PK


def test_pairwise_adapter_keeps_public_json_payload_unchanged() -> None:
    result = analyze_names(
        ["clarithromycin", "ondansetron"],
        as_json_payload=True,
    )

    assert result.ok
    assert "mechanism_pipeline" in result.payload
    assert "pairwise_mechanism_adapter" not in result.payload