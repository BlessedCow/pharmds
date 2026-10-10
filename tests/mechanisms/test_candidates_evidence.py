from core.mechanisms.candidates import find_interaction_candidates
from core.mechanisms.effects import MechanismEffect
from core.mechanisms.registry import MECHANISM_PD_EFFECT


def test_shared_pd_effect_candidate_includes_complete_evidence_trace():
    effects = [
        MechanismEffect(
            source_drug="clarithromycin",
            mechanism=MECHANISM_PD_EFFECT,
            effect_id="nausea",
        ),
        MechanismEffect(
            source_drug="fluconazole",
            mechanism=MECHANISM_PD_EFFECT,
            effect_id="nausea",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    candidate = next(
        candidate
        for candidate in candidates
        if candidate.effect_id == "nausea"
    )

    trace = candidate.metadata["evidence_trace"]

    assert trace["trace_type"] == "additive_pd_effect"
    assert trace["effect_id"] == "nausea"
    assert trace["drug_ids"] == ["clarithromycin", "fluconazole"]
    assert trace["overall_evidence_status"] == "complete"

    claim_ids = {
        claim["claim_id"]
        for drug_item in trace["drugs"]
        for claim in drug_item["claims"]
    }

    assert "claim_clarithromycin_pd_effect_nausea_001" in claim_ids
    assert "claim_fluconazole_pd_effect_nausea_001" in claim_ids


def test_shared_pd_effect_candidate_includes_partial_evidence_trace():
    effects = [
        MechanismEffect(
            source_drug="clarithromycin",
            mechanism=MECHANISM_PD_EFFECT,
            effect_id="nausea",
        ),
        MechanismEffect(
            source_drug="alprazolam",
            mechanism=MECHANISM_PD_EFFECT,
            effect_id="nausea",
        ),
    ]

    candidates = find_interaction_candidates(effects)

    candidate = next(
        candidate
        for candidate in candidates
        if candidate.effect_id == "nausea"
    )

    trace = candidate.metadata["evidence_trace"]

    assert trace["overall_evidence_status"] == "partial"

    statuses = {
        item["drug_id"]: item["evidence_status"]
        for item in trace["drugs"]
    }

    assert statuses["clarithromycin"] == "present"
    assert statuses["alprazolam"] == "missing"