"""Regression inventory for known differences between pairwise engines.

Classification describes the shape of a disagreement, not clinical correctness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

import pytest

from tests.mechanisms.test_pairwise_comparison_harness import (
    KNOWN_GAP_SCENARIOS,
    PairwiseComparisonScenario,
    _mechanism_concepts_for,
    _old_pairwise_rule_ids_for,
)

DiscrepancyKind = Literal[
    "curated_pair_coverage",
    "threshold_policy_difference",
    "mechanism_concept_difference",
    "composite_policy_coverage",
]


@dataclass(frozen=True)
class ClassifiedDiscrepancy:
    scenario_id: str
    kind: DiscrepancyKind
    rationale: str
    requires_clinical_review: bool = True


CLASSIFIED_DISCREPANCIES: tuple[ClassifiedDiscrepancy, ...] = (
    ClassifiedDiscrepancy(
        "old-only-curated-absorption-pair",
        "curated_pair_coverage",
        "Curated doxycycline/calcium rule has no recorded mechanism counterpart.",
    ),
    ClassifiedDiscrepancy(
        "old-only-curated-anticoagulation-pair",
        "curated_pair_coverage",
        "Curated doxycycline/warfarin rule has no recorded mechanism counterpart.",
    ),
    ClassifiedDiscrepancy(
        "mechanism-only-low-plus-medium-qt-threshold-gap",
        "threshold_policy_difference",
        (
            "A mechanism QT concept is present where the legacy PD "
            "threshold does not fire."
        ),
    ),
    ClassifiedDiscrepancy(
        "old-pair-policy-plus-mechanism-only-serotonergic-gap",
        "mechanism_concept_difference",
        "A curated legacy pair rule and a mechanism serotonergic concept differ.",
    ),
    ClassifiedDiscrepancy(
        "old-only-pk-to-pd-cns-amplification-gap",
        "composite_policy_coverage",
        (
            "Legacy composite PK-to-CNS output has no recorded "
            "mechanism policy counterpart."
        ),
    ),
)


def _scenario_by_id() -> dict[str, PairwiseComparisonScenario]:
    return {
        param.id: cast(PairwiseComparisonScenario, param.values[0])
        for param in KNOWN_GAP_SCENARIOS
        if isinstance(param.id, str)
    }


def test_every_known_gap_has_one_review_classification() -> None:
    scenario_ids = set(_scenario_by_id())
    classified_ids = [entry.scenario_id for entry in CLASSIFIED_DISCREPANCIES]

    assert len(classified_ids) == len(set(classified_ids))
    assert set(classified_ids) == scenario_ids
    assert all(entry.rationale.strip() for entry in CLASSIFIED_DISCREPANCIES)
    assert all(entry.requires_clinical_review for entry in CLASSIFIED_DISCREPANCIES)


@pytest.mark.parametrize(
    "entry",
    CLASSIFIED_DISCREPANCIES,
    ids=lambda entry: entry.scenario_id,
)
def test_classified_difference_remains_visible(
    entry: ClassifiedDiscrepancy,
) -> None:
    scenario = _scenario_by_id()[entry.scenario_id]
    legacy_ids = _old_pairwise_rule_ids_for(scenario.drug_names)
    mechanism_concepts = _mechanism_concepts_for(scenario.drug_names)

    assert scenario.known_old_only_rule_ids.issubset(legacy_ids)
    assert scenario.known_mechanism_only_concepts.issubset(mechanism_concepts)
    assert scenario.known_old_only_rule_ids or scenario.known_mechanism_only_concepts

    if entry.kind == "curated_pair_coverage":
        assert scenario.known_old_only_rule_ids
        assert not scenario.known_mechanism_only_concepts
    elif entry.kind == "threshold_policy_difference":
        assert not scenario.known_old_only_rule_ids
        assert scenario.known_mechanism_only_concepts
    elif entry.kind == "mechanism_concept_difference":
        assert scenario.known_old_only_rule_ids
        assert scenario.known_mechanism_only_concepts
    elif entry.kind == "composite_policy_coverage":
        assert "COMP_PK_UP_CNS_DEP" in scenario.known_old_only_rule_ids
        assert not scenario.known_mechanism_only_concepts
