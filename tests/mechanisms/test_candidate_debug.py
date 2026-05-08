from core.mechanisms.candidate_debug import (
    format_interaction_candidate,
    format_interaction_candidates,
)
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
    InteractionCandidate,
)


def test_format_interaction_candidate_with_target():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_ENZYME_INHIBITION,
        precipitant_drug="bupropion",
        object_drug="vortioxetine",
        target="CYP2D6",
    )

    assert format_interaction_candidate(candidate) == (
        "ENZYME_INHIBITION_EXPOSURE: "
        "bupropion -> vortioxetine via CYP2D6"
    )


def test_format_interaction_candidate_with_effect_id():
    candidate = InteractionCandidate(
        candidate_type=CANDIDATE_PD_SHARED_EFFECT,
        precipitant_drug="fluconazole",
        object_drug="vortioxetine",
        effect_id="nausea",
    )

    assert format_interaction_candidate(candidate) == (
        "PD_SHARED_EFFECT: fluconazole + vortioxetine via nausea"
    )


def test_format_interaction_candidates_formats_multiple():
    candidates = [
        InteractionCandidate(
            candidate_type=CANDIDATE_ENZYME_INHIBITION,
            precipitant_drug="bupropion",
            object_drug="vortioxetine",
            target="CYP2D6",
        ),
        InteractionCandidate(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
    ]

    assert format_interaction_candidates(candidates) == [
        (
            "ENZYME_INHIBITION_EXPOSURE: "
            "bupropion -> vortioxetine via CYP2D6"
        ),
        "PD_SHARED_EFFECT: fluconazole + vortioxetine via nausea",
    ]
