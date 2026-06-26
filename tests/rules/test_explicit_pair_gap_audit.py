from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.cli import DB_PATH, RULE_DIR, connect, load_facts, resolve_drug_ids
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanisms.pipeline import run_mechanism_pipeline
from rules.engine import load_rules

PAIR_POLICY_ONLY = "pair_policy_only"
GENERIC_PD_PARTIAL = "generic_pd_partial"
GENERIC_PK_WITH_PAIR_POLICY = "generic_pk_with_pair_policy"


@dataclass(frozen=True)
class ExplicitPairGapCase:
    rule_id: str
    drug_names: tuple[str, str]
    expected_candidate_keys: frozenset[tuple[str, str, str, str | None, str | None]]
    coverage_classification: str


EXPLICIT_PAIR_GAP_CASES = [
    ExplicitPairGapCase(
        rule_id="PK_DOXYCYCLINE_AMOXICILLIN",
        drug_names=("doxycycline", "amoxicillin"),
        expected_candidate_keys=frozenset(),
        coverage_classification=PAIR_POLICY_ONLY,
    ),
    ExplicitPairGapCase(
        rule_id="PK_DOXYCYCLINE_CALCIUM_CARBONATE",
        drug_names=("doxycycline", "calcium carbonate"),
        expected_candidate_keys=frozenset(),
        coverage_classification=PAIR_POLICY_ONLY,
    ),
    ExplicitPairGapCase(
        rule_id="PK_DOXYCYCLINE_WARFARIN",
        drug_names=("doxycycline", "warfarin"),
        expected_candidate_keys=frozenset(),
        coverage_classification=PAIR_POLICY_ONLY,
    ),
    ExplicitPairGapCase(
        rule_id="PK_LISDEXAMFETAMINE_FLUOXETINE",
        drug_names=("lisdexamfetamine", "fluoxetine"),
        expected_candidate_keys=frozenset(
            {
                (
                    CANDIDATE_PD_SHARED_EFFECT,
                    "fluoxetine",
                    "lisdexamfetamine",
                    None,
                    "serotonergic",
                )
            }
        ),
        coverage_classification=GENERIC_PD_PARTIAL,
    ),
    ExplicitPairGapCase(
        rule_id="PK_METHADONE_CARBAMAZEPINE",
        drug_names=("methadone", "carbamazepine"),
        expected_candidate_keys=frozenset(
            {
                (
                    CANDIDATE_ENZYME_INDUCTION,
                    "carbamazepine",
                    "methadone",
                    "CYP2C19",
                    None,
                ),
                (
                    CANDIDATE_ENZYME_INDUCTION,
                    "carbamazepine",
                    "methadone",
                    "CYP2C9",
                    None,
                ),
                (
                    CANDIDATE_ENZYME_INDUCTION,
                    "carbamazepine",
                    "methadone",
                    "CYP3A4",
                    None,
                ),
                (
                    CANDIDATE_PD_SHARED_EFFECT,
                    "carbamazepine",
                    "methadone",
                    None,
                    "CNS_depression",
                ),
            }
        ),
        coverage_classification=GENERIC_PK_WITH_PAIR_POLICY,
    ),
    ExplicitPairGapCase(
        rule_id="PK_METHADONE_FLUOXETINE",
        drug_names=("methadone", "fluoxetine"),
        expected_candidate_keys=frozenset(
            {
                (
                    CANDIDATE_ENZYME_INHIBITION,
                    "fluoxetine",
                    "methadone",
                    "CYP2D6",
                    None,
                ),
                (
                    CANDIDATE_PD_SHARED_EFFECT,
                    "fluoxetine",
                    "methadone",
                    None,
                    "serotonergic",
                ),
            }
        ),
        coverage_classification=GENERIC_PK_WITH_PAIR_POLICY,
    ),
    ExplicitPairGapCase(
        rule_id="PK_VIBEGRON_DIGOXIN",
        drug_names=("vibegron", "digoxin"),
        expected_candidate_keys=frozenset(),
        coverage_classification=PAIR_POLICY_ONLY,
    ),
]

ANTIBACTERIAL_EFFECT_POLICY_NOT_MODELED = (
    "antibacterial_effect_policy_not_modeled"
)
ABSORPTION_OR_CHELATION_NOT_MODELED = "absorption_or_chelation_not_modeled"
ANTICOAGULATION_EFFECT_POLICY_NOT_MODELED = (
    "anticoagulation_effect_policy_not_modeled"
)
STIMULANT_EXPOSURE_POLICY_NOT_MODELED = "stimulant_exposure_policy_not_modeled"
OPIOID_WITHDRAWAL_POLICY_NOT_MODELED = "opioid_withdrawal_policy_not_modeled"
OPIOID_TOXICITY_POLICY_NOT_MODELED = "opioid_toxicity_policy_not_modeled"
DIGOXIN_EXPOSURE_POLICY_NOT_MODELED = "digoxin_exposure_policy_not_modeled"

EXPLICIT_PAIR_GAP_REASONS = {
    "PK_DOXYCYCLINE_AMOXICILLIN": ANTIBACTERIAL_EFFECT_POLICY_NOT_MODELED,
    "PK_DOXYCYCLINE_CALCIUM_CARBONATE": ABSORPTION_OR_CHELATION_NOT_MODELED,
    "PK_DOXYCYCLINE_WARFARIN": ANTICOAGULATION_EFFECT_POLICY_NOT_MODELED,
    "PK_LISDEXAMFETAMINE_FLUOXETINE": STIMULANT_EXPOSURE_POLICY_NOT_MODELED,
    "PK_METHADONE_CARBAMAZEPINE": OPIOID_WITHDRAWAL_POLICY_NOT_MODELED,
    "PK_METHADONE_FLUOXETINE": OPIOID_TOXICITY_POLICY_NOT_MODELED,
    "PK_VIBEGRON_DIGOXIN": DIGOXIN_EXPOSURE_POLICY_NOT_MODELED,
}

EXPLICIT_PAIR_GAP_REASON_TEXT = {
    "PK_DOXYCYCLINE_AMOXICILLIN": ("antagonize", "antibacterial"),
    "PK_DOXYCYCLINE_CALCIUM_CARBONATE": ("chelation", "absorption"),
    "PK_DOXYCYCLINE_WARFARIN": ("anticoagulant", "bleeding"),
    "PK_LISDEXAMFETAMINE_FLUOXETINE": ("cyp2d6", "stimulant"),
    "PK_METHADONE_CARBAMAZEPINE": ("withdrawal", "reduced methadone"),
    "PK_METHADONE_FLUOXETINE": ("opioid toxicity", "respiratory depression"),
    "PK_VIBEGRON_DIGOXIN": ("digoxin", "exposure"),
}

def _pipeline_candidate_keys(
    drug_names: tuple[str, str],
) -> frozenset[tuple[str, str, str, str | None, str | None]]:
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, list(drug_names))
        facts = load_facts(conn, drug_ids, patient_flags={})
    finally:
        conn.close()

    pipeline = run_mechanism_pipeline(drug_ids, facts)
    return frozenset(
        (
            candidate.candidate_type,
            candidate.precipitant_drug,
            candidate.object_drug,
            candidate.target,
            candidate.effect_id,
        )
        for candidate in pipeline.candidates
    )


def test_explicit_pair_gap_audit_covers_all_named_pair_rules() -> None:
    explicit_pair_rule_ids = {
        rule.id
        for rule in load_rules(RULE_DIR)
        if rule.domain == "PK" and "drug_pair" in rule.logic
    }

    assert {case.rule_id for case in EXPLICIT_PAIR_GAP_CASES} == explicit_pair_rule_ids


@pytest.mark.parametrize("case", EXPLICIT_PAIR_GAP_CASES, ids=lambda case: case.rule_id)
def test_explicit_pair_gap_audit_records_current_generic_mechanism_coverage(
    case: ExplicitPairGapCase,
) -> None:
    assert _pipeline_candidate_keys(case.drug_names) == case.expected_candidate_keys


def test_explicit_pair_gap_audit_identifies_pair_policy_required_cases() -> None:
    coverage_by_rule_id = {
        case.rule_id: case.coverage_classification
        for case in EXPLICIT_PAIR_GAP_CASES
    }

    assert coverage_by_rule_id == {
        "PK_DOXYCYCLINE_AMOXICILLIN": PAIR_POLICY_ONLY,
        "PK_DOXYCYCLINE_CALCIUM_CARBONATE": PAIR_POLICY_ONLY,
        "PK_DOXYCYCLINE_WARFARIN": PAIR_POLICY_ONLY,
        "PK_LISDEXAMFETAMINE_FLUOXETINE": GENERIC_PD_PARTIAL,
        "PK_METHADONE_CARBAMAZEPINE": GENERIC_PK_WITH_PAIR_POLICY,
        "PK_METHADONE_FLUOXETINE": GENERIC_PK_WITH_PAIR_POLICY,
        "PK_VIBEGRON_DIGOXIN": PAIR_POLICY_ONLY,
    }
    
def test_explicit_pair_gap_audit_records_pair_specific_gap_reasons() -> None:
    rule_ids = {case.rule_id for case in EXPLICIT_PAIR_GAP_CASES}

    assert set(EXPLICIT_PAIR_GAP_REASONS) == rule_ids
    assert EXPLICIT_PAIR_GAP_REASONS == {
        "PK_DOXYCYCLINE_AMOXICILLIN": (
            ANTIBACTERIAL_EFFECT_POLICY_NOT_MODELED
        ),
        "PK_DOXYCYCLINE_CALCIUM_CARBONATE": (
            ABSORPTION_OR_CHELATION_NOT_MODELED
        ),
        "PK_DOXYCYCLINE_WARFARIN": (
            ANTICOAGULATION_EFFECT_POLICY_NOT_MODELED
        ),
        "PK_LISDEXAMFETAMINE_FLUOXETINE": (
            STIMULANT_EXPOSURE_POLICY_NOT_MODELED
        ),
        "PK_METHADONE_CARBAMAZEPINE": OPIOID_WITHDRAWAL_POLICY_NOT_MODELED,
        "PK_METHADONE_FLUOXETINE": OPIOID_TOXICITY_POLICY_NOT_MODELED,
        "PK_VIBEGRON_DIGOXIN": DIGOXIN_EXPOSURE_POLICY_NOT_MODELED,
    }
    
def _explicit_pair_rule_text_by_id() -> dict[str, str]:
    rule_text_by_id = {}

    for rule in load_rules(RULE_DIR):
        if rule.domain != "PK" or "drug_pair" not in rule.logic:
            continue

        rationale = rule.logic.get("rationale", [])
        rule_text_by_id[rule.id] = " ".join(
            [
                rule.name,
                rule.explanation_template,
                *rule.actions,
                *rationale,
            ]
        ).lower()

    return rule_text_by_id


def test_explicit_pair_gap_reason_text_tracks_rule_content() -> None:
    rule_text_by_id = _explicit_pair_rule_text_by_id()

    assert set(EXPLICIT_PAIR_GAP_REASON_TEXT) == set(EXPLICIT_PAIR_GAP_REASONS)

    for rule_id, expected_snippets in EXPLICIT_PAIR_GAP_REASON_TEXT.items():
        rule_text = rule_text_by_id[rule_id]

        for expected_snippet in expected_snippets:
            assert expected_snippet in rule_text