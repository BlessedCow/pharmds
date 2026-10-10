import pytest

from core.mechanisms.candidates import (
    CANDIDATE_ABSORPTION_INTERFERENCE,
    find_interaction_candidates,
)
from core.mechanisms.effects import MechanismEffect
from core.mechanisms.registry import (
    MECHANISM_ABSORPTION_INTERFERENCE,
    MECHANISM_ABSORPTION_SUSCEPTIBLE,
)


def _effect(drug: str, mechanism: str, target: str) -> MechanismEffect:
    return MechanismEffect(
        source_drug=drug,
        mechanism=mechanism,
        target=target,
        evidence_refs=(f"source_{drug}",),
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_calcium_doxycycline_absorption_candidate(reverse: bool) -> None:
    effects = [
        _effect(
            "doxycycline",
            MECHANISM_ABSORPTION_SUSCEPTIBLE,
            "chelation_polyvalent_cation",
        ),
        _effect(
            "calcium_carbonate",
            MECHANISM_ABSORPTION_INTERFERENCE,
            "chelation_polyvalent_cation",
        ),
    ]
    candidates = find_interaction_candidates(effects[::-1] if reverse else effects)
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.candidate_type == CANDIDATE_ABSORPTION_INTERFERENCE
    assert candidate.object_drug == "doxycycline"
    assert candidate.precipitant_drug == "calcium_carbonate"
    assert candidate.metadata["evidence_refs"] == [
        "source_calcium_carbonate",
        "source_doxycycline",
    ]


def test_absorption_mechanisms_do_not_cross_match() -> None:
    effects = [
        _effect("drug_a", MECHANISM_ABSORPTION_SUSCEPTIBLE, "gastric_ph"),
        _effect(
            "drug_b", MECHANISM_ABSORPTION_INTERFERENCE, "chelation_polyvalent_cation"
        ),
    ]
    assert find_interaction_candidates(effects) == []


def test_absorption_facts_do_not_generate_self_interactions() -> None:
    effects = [
        _effect("drug_a", MECHANISM_ABSORPTION_SUSCEPTIBLE, "adsorption"),
        _effect("drug_a", MECHANISM_ABSORPTION_INTERFERENCE, "adsorption"),
    ]
    assert find_interaction_candidates(effects) == []


def test_absorption_requires_matching_both_roles() -> None:
    effects = [_effect("drug_a", MECHANISM_ABSORPTION_SUSCEPTIBLE, "adsorption")]
    assert find_interaction_candidates(effects) == []
