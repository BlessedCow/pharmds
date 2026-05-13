from core.mechanisms.arbitration import arbitrate_candidates
from core.mechanisms.candidates import find_interaction_candidates
from core.mechanisms.effects import MechanismEffect
from core.mechanisms.policy import apply_concern_policy
from core.mechanisms.registry import MECHANISM_PD_EFFECT
from core.mechanisms.scoring import score_policy_results
from core.mechanisms.severity import annotate_preliminary_severity


def _pd_nausea_effects():
    return [
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


def test_evidence_trace_propagates_from_candidate_to_arbitration_result():
    candidates = find_interaction_candidates(_pd_nausea_effects())
    arbitration_results = arbitrate_candidates(candidates)

    result = next(
        result
        for result in arbitration_results
        if result.effect_id == "nausea"
    )

    trace = result.metadata["evidence_trace"]

    assert trace["overall_evidence_status"] == "complete"
    assert trace["effect_id"] == "nausea"


def test_evidence_trace_propagates_from_arbitration_to_policy_result():
    candidates = find_interaction_candidates(_pd_nausea_effects())
    arbitration_results = arbitrate_candidates(candidates)
    policy_results = apply_concern_policy(arbitration_results)

    result = next(
        result
        for result in policy_results
        if result.effect_id == "nausea"
    )

    trace = result.metadata["evidence_trace"]

    assert trace["overall_evidence_status"] == "complete"
    assert trace["effect_id"] == "nausea"


def test_evidence_trace_propagates_from_policy_to_scored_concern():
    candidates = find_interaction_candidates(_pd_nausea_effects())
    arbitration_results = arbitrate_candidates(candidates)
    policy_results = apply_concern_policy(arbitration_results)
    scored_concerns = score_policy_results(policy_results)

    result = next(
        result
        for result in scored_concerns
        if result.effect_id == "nausea"
    )

    trace = result.metadata["evidence_trace"]

    assert trace["overall_evidence_status"] == "complete"
    assert trace["effect_id"] == "nausea"


def test_evidence_trace_available_on_severity_annotation_scored_concern():
    candidates = find_interaction_candidates(_pd_nausea_effects())
    arbitration_results = arbitrate_candidates(candidates)
    policy_results = apply_concern_policy(arbitration_results)
    scored_concerns = score_policy_results(policy_results)
    severity_annotations = annotate_preliminary_severity(scored_concerns)

    annotation = next(
        annotation
        for annotation in severity_annotations
        if annotation.scored.effect_id == "nausea"
    )

    trace = annotation.scored.metadata["evidence_trace"]

    assert trace["overall_evidence_status"] == "complete"
    assert trace["effect_id"] == "nausea"


def test_evidence_trace_available_after_manual_pipeline_stages():
    candidates = find_interaction_candidates(_pd_nausea_effects())
    arbitration_results = arbitrate_candidates(candidates)
    policy_results = apply_concern_policy(arbitration_results)
    scored_concerns = score_policy_results(policy_results)
    severity_annotations = annotate_preliminary_severity(scored_concerns)

    annotation = next(
        annotation
        for annotation in severity_annotations
        if annotation.scored.effect_id == "nausea"
    )

    trace = annotation.scored.metadata["evidence_trace"]

    assert trace["trace_type"] == "additive_pd_effect"
    assert trace["overall_evidence_status"] == "complete"
    assert trace["effect_id"] == "nausea"

    claim_ids = {
        claim["claim_id"]
        for drug_item in trace["drugs"]
        for claim in drug_item["claims"]
    }

    assert "claim_clarithromycin_pd_effect_nausea_001" in claim_ids
    assert "claim_fluconazole_pd_effect_nausea_001" in claim_ids