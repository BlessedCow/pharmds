from __future__ import annotations

import pytest

from core.mechanisms.candidates import CANDIDATE_ABSORPTION_INTERFERENCE
from core.mechanisms.pipeline import run_mechanism_pipeline
from tests.mechanisms.support import load_drug_facts


@pytest.mark.parametrize("names", [
    ["doxycycline", "calcium carbonate"],
    ["calcium carbonate", "doxycycline"],
])
def test_curated_absorption_roles_reach_pipeline(names: list[str]) -> None:
    drug_ids, facts = load_drug_facts(names)
    pipeline = run_mechanism_pipeline(drug_ids, facts)
    matching = [
        item for item in pipeline.candidates
        if item.candidate_type == CANDIDATE_ABSORPTION_INTERFERENCE
    ]
    assert len(matching) == 1
    assert matching[0].precipitant_drug == "calcium_carbonate"
    assert matching[0].object_drug == "doxycycline"
    assert matching[0].target == "chelation_polyvalent_cation"
    assert any(item.source_concern == "exposure_decrease"
               for item in pipeline.policy_results)


def test_absorption_role_not_loaded_for_unselected_drug() -> None:
    ids, facts = load_drug_facts(["doxycycline"])
    assert "calcium_carbonate" not in facts.absorption_roles
    pipeline = run_mechanism_pipeline(ids, facts)
    assert not any(
        candidate.candidate_type == CANDIDATE_ABSORPTION_INTERFERENCE
        for candidate in pipeline.candidates
    )
