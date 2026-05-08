from core.mechanism_candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_PD_SHARED_EFFECT,
    CANDIDATE_TRANSPORTER_INDUCTION,
    CANDIDATE_TRANSPORTER_INHIBITION,
    InteractionCandidate,
    dedupe_interaction_candidates,
    find_interaction_candidates,
)
from core.mechanism_effect import MechanismEffect
from core.mechanism_registry import (
    MECHANISM_ENZYME_INDUCTION,
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_SUBSTRATE,
    MECHANISM_PD_EFFECT,
    MECHANISM_TRANSPORTER_INDUCTION,
    MECHANISM_TRANSPORTER_INHIBITION,
    MECHANISM_TRANSPORTER_SUBSTRATE,
)


def test_find_enzyme_inhibition_candidate():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_INHIBITION,
            source_drug="bupropion",
            target="CYP2D6",
        ),
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_SUBSTRATE,
            source_drug="vortioxetine",
            target="CYP2D6",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    assert len(candidates) == 1
    assert candidates[0].candidate_type == CANDIDATE_ENZYME_INHIBITION
    assert candidates[0].precipitant_drug == "bupropion"
    assert candidates[0].object_drug == "vortioxetine"
    assert candidates[0].target == "CYP2D6"


def test_find_enzyme_induction_candidate():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_INDUCTION,
            source_drug="rifampin",
            target="CYP3A4",
        ),
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_SUBSTRATE,
            source_drug="vortioxetine",
            target="CYP3A4",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    assert len(candidates) == 1
    assert candidates[0].candidate_type == CANDIDATE_ENZYME_INDUCTION
    assert candidates[0].precipitant_drug == "rifampin"
    assert candidates[0].object_drug == "vortioxetine"
    assert candidates[0].target == "CYP3A4"


def test_find_transporter_inhibition_candidate():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_TRANSPORTER_INHIBITION,
            source_drug="clarithromycin",
            target="P-gp",
        ),
        MechanismEffect(
            mechanism=MECHANISM_TRANSPORTER_SUBSTRATE,
            source_drug="digoxin",
            target="P-gp",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    assert len(candidates) == 1
    assert candidates[0].candidate_type == CANDIDATE_TRANSPORTER_INHIBITION
    assert candidates[0].precipitant_drug == "clarithromycin"
    assert candidates[0].object_drug == "digoxin"
    assert candidates[0].target == "P-gp"


def test_find_transporter_induction_candidate():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_TRANSPORTER_INDUCTION,
            source_drug="rifampin",
            target="P-gp",
        ),
        MechanismEffect(
            mechanism=MECHANISM_TRANSPORTER_SUBSTRATE,
            source_drug="digoxin",
            target="P-gp",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    assert len(candidates) == 1
    assert candidates[0].candidate_type == CANDIDATE_TRANSPORTER_INDUCTION
    assert candidates[0].precipitant_drug == "rifampin"
    assert candidates[0].object_drug == "digoxin"
    assert candidates[0].target == "P-gp"


def test_find_shared_pd_effect_candidate():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="vortioxetine",
            effect_id="nausea",
        ),
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="fluconazole",
            effect_id="nausea",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    assert len(candidates) == 1
    assert candidates[0].candidate_type == CANDIDATE_PD_SHARED_EFFECT
    assert candidates[0].precipitant_drug == "fluconazole"
    assert candidates[0].object_drug == "vortioxetine"
    assert candidates[0].effect_id == "nausea"


def test_no_candidate_for_different_enzyme_targets():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_INHIBITION,
            source_drug="bupropion",
            target="CYP2D6",
        ),
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_SUBSTRATE,
            source_drug="vortioxetine",
            target="CYP3A4",
        ),
    ]

    assert find_interaction_candidates(effects) == []


def test_no_candidate_for_same_drug_enzyme_role_overlap():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_INHIBITION,
            source_drug="example_drug",
            target="CYP2D6",
        ),
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_SUBSTRATE,
            source_drug="example_drug",
            target="CYP2D6",
        ),
    ]

    assert find_interaction_candidates(effects) == []


def test_no_candidate_for_different_pd_effects():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="vortioxetine",
            effect_id="nausea",
        ),
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="bupropion",
            effect_id="seizure_risk",
        ),
    ]

    assert find_interaction_candidates(effects) == []


def test_dedupe_interaction_candidates_preserves_first_seen_order():
    candidates = [
        InteractionCandidate(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
        InteractionCandidate(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            precipitant_drug="fluconazole",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
        InteractionCandidate(
            candidate_type=CANDIDATE_PD_SHARED_EFFECT,
            precipitant_drug="clarithromycin",
            object_drug="vortioxetine",
            effect_id="nausea",
        ),
    ]

    deduped = dedupe_interaction_candidates(candidates)

    assert len(deduped) == 2
    assert deduped[0].precipitant_drug == "fluconazole"
    assert deduped[1].precipitant_drug == "clarithromycin"