from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from app.cli import DB_PATH, connect, load_facts, resolve_drug_ids
from app.service import analyze_names
from core.mechanisms.pairwise_adapter import (
    PAIRWISE_ADAPTER_DOMAIN_PD,
    PAIRWISE_ADAPTER_DOMAIN_PK,
    PairwiseMechanismConcern,
    adapt_mechanism_pipeline_to_pairwise,
)
from core.mechanisms.pipeline import run_mechanism_pipeline


@dataclass(frozen=True)
class PairwiseComparisonConcept:
    domain: str
    concern_id: str
    object_drug: str
    source_concern: str


@dataclass(frozen=True)
class PairwiseComparisonScenario:
    drug_names: tuple[str, ...]
    old_rule_ids: frozenset[str]
    expected_shared_concepts: frozenset[PairwiseComparisonConcept]
    known_old_only_rule_ids: frozenset[str] = frozenset()
    known_mechanism_only_concepts: frozenset[
        PairwiseComparisonConcept
    ] = frozenset()


EXACT_PARITY_SCENARIOS = [
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("clarithromycin", "midazolam"),
            old_rule_ids=frozenset({"PK_CYP3A4_STRONG_INHIB"}),
            expected_shared_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain=PAIRWISE_ADAPTER_DOMAIN_PK,
                        concern_id="CYP3A4",
                        object_drug="midazolam",
                        source_concern="exposure_increase",
                    )
                }
            ),
        ),
        id="pk-cyp3a4-inhibition",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("bupropion", "vortioxetine"),
            old_rule_ids=frozenset({"PK_CYP2D6_INHIB_SUBSTRATE"}),
            expected_shared_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain=PAIRWISE_ADAPTER_DOMAIN_PK,
                        concern_id="CYP2D6",
                        object_drug="vortioxetine",
                        source_concern="exposure_increase",
                    )
                }
            ),
        ),
        id="pk-cyp2d6-inhibition",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("clarithromycin", "ondansetron"),
            old_rule_ids=frozenset({"PD_QT_ADDITIVE"}),
            expected_shared_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain=PAIRWISE_ADAPTER_DOMAIN_PD,
                        concern_id="QT_prolongation",
                        object_drug="ondansetron",
                        source_concern="additive_pd_effect",
                    )
                }
            ),
        ),
        id="pd-qt-additive",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("alprazolam", "gabapentin"),
            old_rule_ids=frozenset({"PD_CNS_DEP_ADDITIVE"}),
            expected_shared_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain=PAIRWISE_ADAPTER_DOMAIN_PD,
                        concern_id="CNS_depression",
                        object_drug="gabapentin",
                        source_concern="additive_pd_effect",
                    )
                }
            ),
        ),
        id="pd-cns-depression-additive",
    ),
]


KNOWN_GAP_SCENARIOS = [
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("doxycycline", "calcium carbonate"),
            old_rule_ids=frozenset({"PK_DOXYCYCLINE_CALCIUM_CARBONATE"}),
            expected_shared_concepts=frozenset(),
            known_old_only_rule_ids=frozenset(
                {"PK_DOXYCYCLINE_CALCIUM_CARBONATE"},
            ),
        ),
        id="old-only-curated-absorption-pair",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("doxycycline", "warfarin"),
            old_rule_ids=frozenset({"PK_DOXYCYCLINE_WARFARIN"}),
            expected_shared_concepts=frozenset(),
            known_old_only_rule_ids=frozenset({"PK_DOXYCYCLINE_WARFARIN"}),
        ),
        id="old-only-curated-anticoagulation-pair",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("fluconazole", "ondansetron"),
            old_rule_ids=frozenset(),
            expected_shared_concepts=frozenset(),
            known_mechanism_only_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain=PAIRWISE_ADAPTER_DOMAIN_PD,
                        concern_id="QT_prolongation",
                        object_drug="ondansetron",
                        source_concern="additive_pd_effect",
                    )
                }
            ),
        ),
        id="mechanism-only-low-plus-medium-qt-threshold-gap",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("lisdexamfetamine", "fluoxetine"),
            old_rule_ids=frozenset({"PK_LISDEXAMFETAMINE_FLUOXETINE"}),
            expected_shared_concepts=frozenset(),
            known_old_only_rule_ids=frozenset(
                {"PK_LISDEXAMFETAMINE_FLUOXETINE"},
            ),
            known_mechanism_only_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain="unknown",
                        concern_id="serotonergic",
                        object_drug="lisdexamfetamine",
                        source_concern="additive_pd_effect",
                    )
                }
            ),
        ),
        id="old-pair-policy-plus-mechanism-only-serotonergic-gap",
    ),
    pytest.param(
        PairwiseComparisonScenario(
            drug_names=("alprazolam", "clarithromycin"),
            old_rule_ids=frozenset(
                {"PK_CYP3A4_STRONG_INHIB", "COMP_PK_UP_CNS_DEP"},
            ),
            expected_shared_concepts=frozenset(
                {
                    PairwiseComparisonConcept(
                        domain=PAIRWISE_ADAPTER_DOMAIN_PK,
                        concern_id="CYP3A4",
                        object_drug="alprazolam",
                        source_concern="exposure_increase",
                    )
                }
            ),
            known_old_only_rule_ids=frozenset({"COMP_PK_UP_CNS_DEP"}),
        ),
        id="old-only-pk-to-pd-cns-amplification-gap",
    ),
]


def _old_pairwise_rule_ids_for(drug_names: tuple[str, ...]) -> set[str]:
    result = analyze_names(list(drug_names), as_json_payload=True)

    assert result.ok

    return {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for domain in ("pk", "pd")
        for hit in pair[domain]["hits"]
    }


def _mechanism_pairwise_concerns_for(
    drug_names: tuple[str, ...],
) -> tuple[PairwiseMechanismConcern, ...]:
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, list(drug_names))
        facts = load_facts(conn, drug_ids, patient_flags={})
    finally:
        conn.close()

    pipeline = run_mechanism_pipeline(drug_ids, facts)
    return adapt_mechanism_pipeline_to_pairwise(pipeline)


def _mechanism_concepts_for(
    drug_names: tuple[str, ...],
) -> set[PairwiseComparisonConcept]:
    return {
        PairwiseComparisonConcept(
            domain=concern.domain,
            concern_id=concern.concern_id,
            object_drug=concern.object_drug,
            source_concern=concern.source_concern,
        )
        for concern in _mechanism_pairwise_concerns_for(drug_names)
    }


@pytest.mark.parametrize("scenario", EXACT_PARITY_SCENARIOS)
def test_pairwise_comparison_harness_records_exact_parity_scenarios(
    scenario: PairwiseComparisonScenario,
) -> None:
    old_rule_ids = _old_pairwise_rule_ids_for(scenario.drug_names)
    mechanism_concepts = _mechanism_concepts_for(scenario.drug_names)

    assert scenario.old_rule_ids.issubset(old_rule_ids)
    assert scenario.expected_shared_concepts.issubset(mechanism_concepts)
    assert not scenario.known_old_only_rule_ids
    assert not scenario.known_mechanism_only_concepts


@pytest.mark.parametrize("scenario", KNOWN_GAP_SCENARIOS)
def test_pairwise_comparison_harness_records_known_gap_scenarios(
    scenario: PairwiseComparisonScenario,
) -> None:
    old_rule_ids = _old_pairwise_rule_ids_for(scenario.drug_names)
    mechanism_concepts = _mechanism_concepts_for(scenario.drug_names)

    assert scenario.old_rule_ids.issubset(old_rule_ids)
    assert scenario.expected_shared_concepts.issubset(mechanism_concepts)
    assert scenario.known_old_only_rule_ids.issubset(old_rule_ids)
    assert scenario.known_old_only_rule_ids or (
        scenario.known_mechanism_only_concepts
    )
    assert scenario.known_mechanism_only_concepts.issubset(
        mechanism_concepts,
    )


def test_pairwise_comparison_harness_keeps_exact_and_gap_scenarios_separate() -> None:
    exact_case_ids = {
        param.id
        for param in EXACT_PARITY_SCENARIOS
        if param.id is not None
    }
    gap_case_ids = {
        param.id
        for param in KNOWN_GAP_SCENARIOS
        if param.id is not None
    }

    assert exact_case_ids
    assert gap_case_ids
    assert exact_case_ids.isdisjoint(gap_case_ids)


def test_pairwise_comparison_harness_keeps_known_gap_inventory_explicit() -> None:
    known_old_only_rule_ids = {
        rule_id
        for param in KNOWN_GAP_SCENARIOS
        for rule_id in param.values[0].known_old_only_rule_ids
    }
    known_mechanism_only_concepts = {
        concept
        for param in KNOWN_GAP_SCENARIOS
        for concept in param.values[0].known_mechanism_only_concepts
    }

    assert known_old_only_rule_ids == {
        "PK_DOXYCYCLINE_CALCIUM_CARBONATE",
        "PK_DOXYCYCLINE_WARFARIN",
        "PK_LISDEXAMFETAMINE_FLUOXETINE",
        "COMP_PK_UP_CNS_DEP",
    }
    assert known_mechanism_only_concepts == {
        PairwiseComparisonConcept(
            domain=PAIRWISE_ADAPTER_DOMAIN_PD,
            concern_id="QT_prolongation",
            object_drug="ondansetron",
            source_concern="additive_pd_effect",
        ),
        PairwiseComparisonConcept(
            domain="unknown",
            concern_id="serotonergic",
            object_drug="lisdexamfetamine",
            source_concern="additive_pd_effect",
        ),
    }


def test_pairwise_comparison_harness_audit_doc_tracks_scope() -> None:
    audit_text = Path(
        "docs/audits/pairwise_comparison_harness.md",
    ).read_text(encoding="utf-8")

    assert "# Pairwise comparison harness audit" in audit_text
    assert "Exact parity" in audit_text
    assert "Known gaps" in audit_text
    assert "`PK_CYP3A4_STRONG_INHIB`" in audit_text
    assert "`PD_QT_ADDITIVE`" in audit_text
    assert "No public CLI, Streamlit, or JSON output is changed" in audit_text