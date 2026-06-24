from __future__ import annotations

import pytest

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_DECREASE,
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SHARED_PD_EFFECT,
    AGGREGATE_TOLERABILITY_CONCERN,
)
from core.mechanisms.pipeline import run_mechanism_pipeline
from rules.engine import evaluate_all, load_rules

REPRESENTATIVE_PAIRWISE_PARITY_CASES = [
    pytest.param(
        ["clarithromycin", "midazolam"],
        "PK_CYP3A4_STRONG_INHIB",
        AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        "midazolam",
        ("CYP3A4",),
        None,
        id="pk-cyp3a4-inhibition",
    ),
    pytest.param(
        ["bupropion", "vortioxetine"],
        "PK_CYP2D6_INHIB_SUBSTRATE",
        AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        "vortioxetine",
        ("CYP2D6",),
        None,
        id="pk-cyp2d6-inhibition",
    ),
    pytest.param(
        ["rifampin", "midazolam"],
        "PK_CYP3A4_STRONG_INDUC",
        AGGREGATE_OBJECT_EXPOSURE_DECREASE,
        "midazolam",
        ("CYP3A4",),
        None,
        id="pk-cyp3a4-induction",
    ),
    pytest.param(
        ["clarithromycin", "digoxin"],
        "PK_PGP_INHIB_DIGOXIN",
        AGGREGATE_OBJECT_EXPOSURE_INCREASE,
        "digoxin",
        ("P-gp",),
        None,
        id="transporter-pgp-inhibition",
    ),
    pytest.param(
        ["rifampin", "digoxin"],
        "PK_PGP_INDUC_DIGOXIN",
        AGGREGATE_OBJECT_EXPOSURE_DECREASE,
        "digoxin",
        ("P-gp",),
        None,
        id="transporter-pgp-induction",
    ),
    pytest.param(
        ["clarithromycin", "ondansetron"],
        "PD_QT_ADDITIVE",
        AGGREGATE_SHARED_PD_EFFECT,
        "QT_prolongation",
        (),
        "QT_prolongation",
        id="shared-pd-qt-prolongation",
    ),
    pytest.param(
        ["verapamil", "digoxin"],
        "PD_BRADYCARDIA_ADDITIVE",
        AGGREGATE_SHARED_PD_EFFECT,
        "bradycardia",
        (),
        "bradycardia",
        id="shared-pd-bradycardia",
    ),
]


def _baseline_outputs(drug_names: list[str]):
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
        facts = load_facts(conn, drug_ids, patient_flags={})
    finally:
        conn.close()

    rule_hits = evaluate_all(load_rules(RULE_DIR), facts, drug_ids)
    pipeline = run_mechanism_pipeline(drug_ids, facts)
    return rule_hits, pipeline


@pytest.mark.parametrize(
    (
        "drug_names",
        "expected_rule_id",
        "expected_aggregate_type",
        "expected_anchor",
        "expected_targets",
        "expected_effect_id",
    ),
    REPRESENTATIVE_PAIRWISE_PARITY_CASES,
)
def test_mechanism_pipeline_matches_representative_pairwise_concern_concepts(
    drug_names: list[str],
    expected_rule_id: str,
    expected_aggregate_type: str,
    expected_anchor: str,
    expected_targets: tuple[str, ...],
    expected_effect_id: str | None,
) -> None:
    rule_hits, pipeline = _baseline_outputs(drug_names)

    assert expected_rule_id in {hit.rule_id for hit in rule_hits}
    assert any(
        aggregate.aggregate_type == expected_aggregate_type
        and aggregate.anchor == expected_anchor
        and aggregate.targets == expected_targets
        and aggregate.effect_id == expected_effect_id
        for aggregate in pipeline.aggregate_concerns
    )
    
REPRESENTATIVE_EXPLICIT_PAIR_BASELINE_CASES = [
    pytest.param(
        ["doxycycline", "amoxicillin"],
        {"PK_DOXYCYCLINE_AMOXICILLIN"},
        set(),
        id="explicit-pair-doxycycline-amoxicillin",
    ),
    pytest.param(
        ["doxycycline", "calcium carbonate"],
        {"PK_DOXYCYCLINE_CALCIUM_CARBONATE"},
        set(),
        id="explicit-pair-doxycycline-calcium-carbonate",
    ),
    pytest.param(
        ["doxycycline", "warfarin"],
        {"PK_DOXYCYCLINE_WARFARIN"},
        set(),
        id="explicit-pair-doxycycline-warfarin",
    ),
    pytest.param(
        ["lisdexamfetamine", "fluoxetine"],
        {"PK_LISDEXAMFETAMINE_FLUOXETINE"},
        {(AGGREGATE_SHARED_PD_EFFECT, "serotonergic", (), "serotonergic")},
        id="explicit-pair-lisdexamfetamine-fluoxetine",
    ),
    pytest.param(
        ["methadone", "carbamazepine"],
        {"PK_CYP3A4_STRONG_INDUC", "PK_METHADONE_CARBAMAZEPINE"},
        {
            (
                AGGREGATE_OBJECT_EXPOSURE_DECREASE,
                "methadone",
                ("CYP2C19", "CYP2C9", "CYP3A4"),
                None,
            ),
            (
                AGGREGATE_SHARED_PD_EFFECT,
                "CNS_depression",
                (),
                "CNS_depression",
            ),
            (
                AGGREGATE_TOLERABILITY_CONCERN,
                "tolerability_concern",
                (),
                "CNS_depression",
            ),
        },
        id="explicit-pair-methadone-carbamazepine",
    ),
    pytest.param(
        ["methadone", "fluoxetine"],
        {"PK_CYP2D6_INHIB_SUBSTRATE", "PK_METHADONE_FLUOXETINE"},
        {
            (
                AGGREGATE_OBJECT_EXPOSURE_INCREASE,
                "methadone",
                ("CYP2D6",),
                None,
            ),
            (AGGREGATE_SHARED_PD_EFFECT, "serotonergic", (), "serotonergic"),
        },
        id="explicit-pair-methadone-fluoxetine",
    ),
    pytest.param(
        ["vibegron", "digoxin"],
        {"PK_VIBEGRON_DIGOXIN"},
        set(),
        id="explicit-pair-vibegron-digoxin",
    ),
]


def _aggregate_concern_keys(
    pipeline,
) -> set[tuple[str, str, tuple[str, ...], str | None]]:
    return {
        (
            aggregate.aggregate_type,
            aggregate.anchor,
            aggregate.targets,
            aggregate.effect_id,
        )
        for aggregate in pipeline.aggregate_concerns
    }


@pytest.mark.parametrize(
    ("drug_names", "expected_rule_ids", "expected_aggregate_keys"),
    REPRESENTATIVE_EXPLICIT_PAIR_BASELINE_CASES,
)
def test_explicit_pair_rules_record_current_mechanism_pipeline_baseline(
    drug_names: list[str],
    expected_rule_ids: set[str],
    expected_aggregate_keys: set[tuple[str, str, tuple[str, ...], str | None]],
) -> None:
    rule_hits, pipeline = _baseline_outputs(drug_names)

    assert expected_rule_ids.issubset({hit.rule_id for hit in rule_hits})
    assert _aggregate_concern_keys(pipeline) == expected_aggregate_keys