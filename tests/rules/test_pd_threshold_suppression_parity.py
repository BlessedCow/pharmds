from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from app.service import analyze_names
from core.mechanisms.candidates import CANDIDATE_PD_SHARED_EFFECT
from core.mechanisms.pipeline import run_mechanism_pipeline
from core.mechanisms.policy import (
    POLICY_SAFETY_CONCERN,
    POLICY_TOLERABILITY_CONCERN,
)
from rules.engine import evaluate_all, load_rules


@dataclass(frozen=True)
class PdThresholdCase:
    drug_names: tuple[str, str]
    rule_id: str
    effect_id: str
    expected_rule_present: bool
    expected_pipeline_candidate_present: bool


PD_THRESHOLD_CASES = [
    pytest.param(
        PdThresholdCase(
            drug_names=("citalopram", "ondansetron"),
            rule_id="PD_QT_ADDITIVE",
            effect_id="QT_prolongation",
            expected_rule_present=True,
            expected_pipeline_candidate_present=True,
        ),
        id="qt-high-plus-medium-meets-medium-threshold",
    ),
    pytest.param(
        PdThresholdCase(
            drug_names=("fluconazole", "ondansetron"),
            rule_id="PD_QT_ADDITIVE",
            effect_id="QT_prolongation",
            expected_rule_present=False,
            expected_pipeline_candidate_present=True,
        ),
        id="qt-low-plus-medium-blocked-by-old-medium-threshold",
    ),
    pytest.param(
        PdThresholdCase(
            drug_names=("fluoxetine", "sertraline"),
            rule_id="PD_SEROTONERGIC_ADDITIVE",
            effect_id="serotonergic",
            expected_rule_present=True,
            expected_pipeline_candidate_present=True,
        ),
        id="serotonergic-medium-plus-medium-meets-medium-threshold",
    ),
    pytest.param(
        PdThresholdCase(
            drug_names=("lisdexamfetamine", "fluoxetine"),
            rule_id="PD_SEROTONERGIC_ADDITIVE",
            effect_id="serotonergic",
            expected_rule_present=False,
            expected_pipeline_candidate_present=True,
        ),
        id="serotonergic-low-plus-medium-blocked-by-old-medium-threshold",
    ),
    pytest.param(
        PdThresholdCase(
            drug_names=("alprazolam", "gabapentin"),
            rule_id="PD_CNS_DEP_ADDITIVE",
            effect_id="CNS_depression",
            expected_rule_present=True,
            expected_pipeline_candidate_present=True,
        ),
        id="cns-depression-medium-plus-medium-meets-medium-threshold",
    ),
    pytest.param(
        PdThresholdCase(
            drug_names=("aripiprazole", "gabapentin"),
            rule_id="PD_CNS_DEP_ADDITIVE",
            effect_id="CNS_depression",
            expected_rule_present=False,
            expected_pipeline_candidate_present=True,
        ),
        id="cns-depression-low-plus-medium-blocked-by-old-medium-threshold",
    ),
]


@dataclass(frozen=True)
class QtSuppressionCase:
    drug_names: tuple[str, str]
    expected_rule_ids: frozenset[str]
    suppressed_rule_ids: frozenset[str]
    expected_pipeline_qt_policy_count: int


QT_SUPPRESSION_CASES = [
    pytest.param(
        QtSuppressionCase(
            drug_names=("citalopram", "methadone"),
            expected_rule_ids=frozenset(
                {"PD_QT_PROLONGATION_ADDITIVE_HIGH"},
            ),
            suppressed_rule_ids=frozenset({"PD_QT_ADDITIVE"}),
            expected_pipeline_qt_policy_count=1,
        ),
        id="high-qt-rule-suppresses-generic-qt-rule",
    ),
    pytest.param(
        QtSuppressionCase(
            drug_names=("citalopram", "ondansetron"),
            expected_rule_ids=frozenset({"PD_QT_ADDITIVE"}),
            suppressed_rule_ids=frozenset(
                {"PD_QT_PROLONGATION_ADDITIVE_HIGH"},
            ),
            expected_pipeline_qt_policy_count=1,
        ),
        id="medium-qt-rule-remains-when-high-threshold-not-met",
    ),
]

EXPECTED_PD_RULE_MIN_MAGNITUDES = {
    "PD_QT_ADDITIVE": ("QT_prolongation", "medium"),
    "PD_QT_PROLONGATION_ADDITIVE_HIGH": ("QT_prolongation", "high"),
    "PD_SEROTONERGIC_ADDITIVE": ("serotonergic", "medium"),
    "PD_CNS_DEP_ADDITIVE": ("CNS_depression", "medium"),
}

PD_THRESHOLD_SUPPRESSION_AUDIT_DOC = (
    "docs/audits/pd_threshold_suppression_parity.md"
)

def _facts_for(drug_names: tuple[str, ...]):
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, list(drug_names))
        facts = load_facts(conn, drug_ids, patient_flags={})
    finally:
        conn.close()

    return drug_ids, facts


def _rule_ids_for(drug_names: tuple[str, ...]) -> set[str]:
    drug_ids, facts = _facts_for(drug_names)
    return {
        hit.rule_id
        for hit in evaluate_all(load_rules(RULE_DIR), facts, drug_ids)
    }

def _json_payload_for(drug_names: tuple[str, ...]) -> dict:
    result = analyze_names(list(drug_names), as_json_payload=True)

    assert result.ok

    return result.payload


def _json_pd_rule_ids_for(drug_names: tuple[str, ...]) -> set[str]:
    payload = _json_payload_for(drug_names)

    return {
        hit["rule_id"]
        for pair in payload["pairs"]
        for hit in pair["pd"]["hits"]
    }


def _json_pipeline_policy_effect_ids_for(
    drug_names: tuple[str, ...],
) -> list[str]:
    payload = _json_payload_for(drug_names)

    return [
        policy["effect_id"]
        for policy in payload["mechanism_pipeline"]["policy_results"]
        if policy["effect_id"] is not None
    ]

def _pipeline_for(drug_names: tuple[str, ...]):
    drug_ids, facts = _facts_for(drug_names)
    return run_mechanism_pipeline(drug_ids, facts)


def _pipeline_policy_effect_keys(
    drug_names: tuple[str, ...],
) -> set[tuple[str, str, str, str]]:
    pipeline = _pipeline_for(drug_names)
    return {
        (
            policy.policy_concern,
            policy.precipitant_drug,
            policy.object_drug,
            policy.effect_id,
        )
        for policy in pipeline.policy_results
        if policy.effect_id is not None
    }


def _pipeline_candidate_effect_keys(
    drug_names: tuple[str, ...],
) -> set[tuple[str, str, str, str]]:
    pipeline = _pipeline_for(drug_names)
    return {
        (
            candidate.candidate_type,
            candidate.precipitant_drug,
            candidate.object_drug,
            candidate.effect_id,
        )
        for candidate in pipeline.candidates
        if candidate.effect_id is not None
    }


@pytest.mark.parametrize("case", PD_THRESHOLD_CASES)
def test_old_pd_min_magnitude_thresholds_against_mechanism_pipeline_baseline(
    case: PdThresholdCase,
) -> None:
    rule_ids = _rule_ids_for(case.drug_names)
    pipeline_candidate_effect_keys = _pipeline_candidate_effect_keys(
        case.drug_names,
    )
    first_drug, second_drug = sorted(case.drug_names)

    assert (case.rule_id in rule_ids) is case.expected_rule_present
    assert (
        (
            CANDIDATE_PD_SHARED_EFFECT,
            first_drug,
            second_drug,
            case.effect_id,
        )
        in pipeline_candidate_effect_keys
    ) is case.expected_pipeline_candidate_present


@pytest.mark.parametrize("case", QT_SUPPRESSION_CASES)
def test_old_qt_rule_suppression_against_mechanism_policy_baseline(
    case: QtSuppressionCase,
) -> None:
    rule_ids = _rule_ids_for(case.drug_names)
    pipeline_qt_policy_keys = {
        key
        for key in _pipeline_policy_effect_keys(case.drug_names)
        if key[3] == "QT_prolongation"
    }

    assert case.expected_rule_ids.issubset(rule_ids)
    assert rule_ids.isdisjoint(case.suppressed_rule_ids)
    assert len(pipeline_qt_policy_keys) == case.expected_pipeline_qt_policy_count


def test_mechanism_policy_currently_classifies_qt_as_safety_and_cns_as_tolerability(
    ) -> None:
    assert (
        POLICY_SAFETY_CONCERN,
        "fluconazole",
        "ondansetron",
        "QT_prolongation",
    ) in _pipeline_policy_effect_keys(("fluconazole", "ondansetron"))

    assert (
        POLICY_TOLERABILITY_CONCERN,
        "aripiprazole",
        "gabapentin",
        "CNS_depression",
    ) in _pipeline_policy_effect_keys(("aripiprazole", "gabapentin"))


def test_pd_threshold_gap_cases_document_pipeline_is_less_restrictive_than_old_rules(
    ) -> None:
    old_rule_threshold_gap_cases = {
        case.rule_id: case.drug_names
        for case in [param.values[0] for param in PD_THRESHOLD_CASES]
        if not case.expected_rule_present
        and case.expected_pipeline_candidate_present
    }

    assert old_rule_threshold_gap_cases == {
        "PD_QT_ADDITIVE": ("fluconazole", "ondansetron"),
        "PD_SEROTONERGIC_ADDITIVE": (
            "lisdexamfetamine",
            "fluoxetine",
        ),
        "PD_CNS_DEP_ADDITIVE": ("aripiprazole", "gabapentin"),
    }
    
def test_pd_threshold_rule_definitions_keep_expected_min_magnitudes() -> None:
    pd_overlap_by_rule_id = {
        rule.id: rule.logic["pd_overlap"]
        for rule in load_rules(RULE_DIR)
        if "pd_overlap" in rule.logic
    }

    for rule_id, (effect_id, min_magnitude) in (
        EXPECTED_PD_RULE_MIN_MAGNITUDES.items()
    ):
        assert pd_overlap_by_rule_id[rule_id] == {
            "effect_id": effect_id,
            "min_magnitude": min_magnitude,
        }


def test_json_payload_preserves_old_qt_suppression_in_pairwise_pd_hits() -> None:
    pd_rule_ids = _json_pd_rule_ids_for(("citalopram", "methadone"))

    assert "PD_QT_PROLONGATION_ADDITIVE_HIGH" in pd_rule_ids
    assert "PD_QT_ADDITIVE" not in pd_rule_ids


def test_json_payload_preserves_old_pd_threshold_suppression_in_pairwise_hits() -> None:
    assert _json_pd_rule_ids_for(("fluconazole", "ondansetron")) == set()
    assert (
        "QT_prolongation"
        in _json_pipeline_policy_effect_ids_for(
            ("fluconazole", "ondansetron"),
        )
    )


def test_json_payload_keeps_medium_threshold_pairwise_qt_when_high_rule_absent(
    ) -> None:
    pd_rule_ids = _json_pd_rule_ids_for(("citalopram", "ondansetron"))

    assert pd_rule_ids == {"PD_QT_ADDITIVE"}
    assert (
        _json_pipeline_policy_effect_ids_for(
            ("citalopram", "ondansetron"),
        ).count("QT_prolongation")
        == 1
    )


def test_pd_threshold_suppression_audit_doc_tracks_locked_behaviors() -> None:
    from pathlib import Path

    audit_text = Path(PD_THRESHOLD_SUPPRESSION_AUDIT_DOC).read_text(
        encoding="utf-8",
    )

    assert "# PD threshold and suppression parity audit" in audit_text

    for rule_id, (effect_id, min_magnitude) in (
        EXPECTED_PD_RULE_MIN_MAGNITUDES.items()
    ):
        assert f"`{rule_id}`" in audit_text
        assert f"`{effect_id}`" in audit_text
        assert f"`{min_magnitude}`" in audit_text

    assert "`PD_QT_PROLONGATION_ADDITIVE_HIGH`" in audit_text
    assert "`PD_QT_ADDITIVE`" in audit_text
    assert "suppresses" in audit_text