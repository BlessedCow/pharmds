from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.cli import DB_PATH, connect, load_facts, resolve_drug_ids
from app.service import analyze_names
from core.mechanisms.aggregation import AGGREGATE_OBJECT_EXPOSURE_INCREASE
from core.mechanisms.pipeline import run_mechanism_pipeline


@dataclass(frozen=True)
class CompositeParityCase:
    drug_names: tuple[str, ...]
    expected_pk_rule_ids: frozenset[str]
    expected_pd_rule_ids: frozenset[str]
    expected_object_exposure_aggregate: tuple[str, tuple[str, ...]] | None


COMPOSITE_PARITY_CASES = [
    pytest.param(
        CompositeParityCase(
            drug_names=("tacrolimus", "clarithromycin"),
            expected_pk_rule_ids=frozenset(
                {
                    "PK_CYP3A4_STRONG_INHIB",
                    "PK_PGP_INHIB_DIGOXIN",
                    "PK_DUAL_MECH_INCREASE",
                }
            ),
            expected_pd_rule_ids=frozenset(),
            expected_object_exposure_aggregate=(
                "tacrolimus",
                ("CYP3A4", "P-gp"),
            ),
        ),
        id="cyp-plus-pgp-dual-mechanism-exposure-increase",
    ),
    pytest.param(
        CompositeParityCase(
            drug_names=("methadone", "clarithromycin"),
            expected_pk_rule_ids=frozenset({"PK_CYP3A4_STRONG_INHIB"}),
            expected_pd_rule_ids=frozenset(
                {"COMP_PK_UP_CNS_DEP", "PD_QT_ADDITIVE"},
            ),
            expected_object_exposure_aggregate=("methadone", ("CYP3A4",)),
        ),
        id="pk-exposure-increase-amplifies-cns-depression",
    ),
    pytest.param(
        CompositeParityCase(
            drug_names=("alprazolam", "clarithromycin"),
            expected_pk_rule_ids=frozenset({"PK_CYP3A4_STRONG_INHIB"}),
            expected_pd_rule_ids=frozenset({"COMP_PK_UP_CNS_DEP"}),
            expected_object_exposure_aggregate=("alprazolam", ("CYP3A4",)),
        ),
        id="pk-to-pd-cns-amplification-without-shared-pd-rule",
    ),
    pytest.param(
        CompositeParityCase(
            drug_names=("vortioxetine", "fluconazole", "bupropion"),
            expected_pk_rule_ids=frozenset({"PK_CYP2D6_INHIB_SUBSTRATE"}),
            expected_pd_rule_ids=frozenset(),
            expected_object_exposure_aggregate=(
                "vortioxetine",
                ("CYP2C19", "CYP2C9", "CYP2D6"),
            ),
        ),
        id="mechanism-pipeline-records-three-target-exposure-increase",
    ),
]


def _payload_for(drug_names: tuple[str, ...]) -> dict:
    result = analyze_names(list(drug_names), as_json_payload=True)

    assert result.ok

    return result.payload


def _payload_rule_ids_by_domain(
    drug_names: tuple[str, ...],
) -> tuple[set[str], set[str]]:
    payload = _payload_for(drug_names)

    pk_rule_ids = {
        hit["rule_id"]
        for pair in payload["pairs"]
        for hit in pair["pk"]["hits"]
    }
    pd_rule_ids = {
        hit["rule_id"]
        for pair in payload["pairs"]
        for hit in pair["pd"]["hits"]
    }

    return pk_rule_ids, pd_rule_ids


def _pipeline_for(drug_names: tuple[str, ...]):
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, list(drug_names))
        facts = load_facts(conn, drug_ids, patient_flags={})
    finally:
        conn.close()

    return run_mechanism_pipeline(drug_ids, facts)


def _object_exposure_aggregate_keys(
    drug_names: tuple[str, ...],
) -> set[tuple[str, tuple[str, ...]]]:
    pipeline = _pipeline_for(drug_names)

    return {
        (aggregate.anchor, aggregate.targets)
        for aggregate in pipeline.aggregate_concerns
        if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_INCREASE
    }


@pytest.mark.parametrize("case", COMPOSITE_PARITY_CASES)
def test_composite_rule_outputs_against_mechanism_aggregate_baseline(
    case: CompositeParityCase,
) -> None:
    pk_rule_ids, pd_rule_ids = _payload_rule_ids_by_domain(case.drug_names)

    assert case.expected_pk_rule_ids.issubset(pk_rule_ids)
    assert case.expected_pd_rule_ids.issubset(pd_rule_ids)

    if case.expected_object_exposure_aggregate is not None:
        assert case.expected_object_exposure_aggregate in (
            _object_exposure_aggregate_keys(case.drug_names)
        )


def test_mechanism_pipeline_multi_target_exposure_is_not_old_composite_output(
    ) -> None:
    pk_rule_ids, pd_rule_ids = _payload_rule_ids_by_domain(
        ("vortioxetine", "fluconazole", "bupropion"),
    )

    assert "PK_MULTI_MECH_INCREASE" not in pk_rule_ids
    assert "PK_DUAL_MECH_INCREASE_CYP_UGT" not in pk_rule_ids
    assert "COMP_PK_UP_CNS_DEP" not in pd_rule_ids
    assert ("vortioxetine", ("CYP2C19", "CYP2C9", "CYP2D6")) in (
        _object_exposure_aggregate_keys(
            ("vortioxetine", "fluconazole", "bupropion"),
        )
    )


def test_pk_to_pd_composite_remains_old_rule_output_not_mechanism_policy_output(
    ) -> None:
    pk_rule_ids, pd_rule_ids = _payload_rule_ids_by_domain(
        ("alprazolam", "clarithromycin"),
    )
    pipeline = _pipeline_for(("alprazolam", "clarithromycin"))

    assert "PK_CYP3A4_STRONG_INHIB" in pk_rule_ids
    assert "COMP_PK_UP_CNS_DEP" in pd_rule_ids
    assert all(
        policy.effect_id != "CNS_depression"
        for policy in pipeline.policy_results
    )
    assert ("alprazolam", ("CYP3A4",)) in _object_exposure_aggregate_keys(
        ("alprazolam", "clarithromycin"),
    )


def test_composite_rule_parity_audit_doc_tracks_locked_behaviors() -> None:
    audit_text = Path("docs/audits/composite_rule_parity.md").read_text(
        encoding="utf-8",
    )

    assert "# Composite rule parity audit" in audit_text

    for rule_id in (
        "PK_DUAL_MECH_INCREASE",
        "PK_DUAL_MECH_INCREASE_CYP_UGT",
        "PK_DUAL_MECH_INCREASE_UGT_PGP",
        "PK_MULTI_MECH_INCREASE",
        "COMP_PK_UP_CNS_DEP",
    ):
        assert f"`{rule_id}`" in audit_text

    assert "object_exposure_increase_cluster" in audit_text
    assert "PK-to-PD amplification" in audit_text