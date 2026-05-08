from core.mechanisms.aggregation import AGGREGATE_OBJECT_EXPOSURE_INCREASE
from core.mechanisms.arbitration import CONCERN_EXPOSURE_INCREASE
from core.mechanisms.candidates import CANDIDATE_ENZYME_INHIBITION
from core.mechanisms.pipeline import run_mechanism_pipeline
from core.mechanisms.policy import POLICY_MECHANISTIC_CONCERN
from core.mechanisms.registry import (
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_SUBSTRATE,
)
from core.models import Drug, EnzymeRole, Facts


def test_run_mechanism_pipeline_returns_all_stages():
    facts = Facts(
        drugs={
            "bupropion": Drug(
                id="bupropion",
                generic_name="bupropion",
                drug_class="NDRI antidepressant",
                therapeutic_index="moderate",
            ),
            "vortioxetine": Drug(
                id="vortioxetine",
                generic_name="vortioxetine",
                drug_class="serotonin modulator and stimulator",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={
            "bupropion": [
                EnzymeRole(
                    enzyme_id="CYP2D6",
                    role="inhibitor",
                    strength="strong",
                )
            ],
            "vortioxetine": [
                EnzymeRole(
                    enzyme_id="CYP2D6",
                    role="substrate",
                    fraction_metabolized=0.6,
                )
            ],
        },
        transporter_roles={},
        pd_effects={},
    )

    result = run_mechanism_pipeline(
        ["bupropion", "vortioxetine"],
        facts,
    )

    assert len(result.effects) == 2
    assert len(result.candidates) == 1
    assert len(result.arbitration_results) == 1
    assert len(result.policy_results) == 1
    assert len(result.aggregate_concerns) == 1
    assert len(result.scored_concerns) == 1

    effect_keys = {
        (effect.mechanism, effect.source_drug, effect.target)
        for effect in result.effects
    }

    assert (
        MECHANISM_ENZYME_INHIBITION,
        "bupropion",
        "CYP2D6",
    ) in effect_keys
    assert (
        MECHANISM_ENZYME_SUBSTRATE,
        "vortioxetine",
        "CYP2D6",
    ) in effect_keys

    candidate = result.candidates[0]
    assert candidate.candidate_type == CANDIDATE_ENZYME_INHIBITION
    assert candidate.precipitant_drug == "bupropion"
    assert candidate.object_drug == "vortioxetine"
    assert candidate.target == "CYP2D6"

    arbitration = result.arbitration_results[0]
    assert arbitration.concern == CONCERN_EXPOSURE_INCREASE
    assert arbitration.precipitant_drug == "bupropion"
    assert arbitration.object_drug == "vortioxetine"
    assert arbitration.target == "CYP2D6"

    policy = result.policy_results[0]
    assert policy.policy_concern == POLICY_MECHANISTIC_CONCERN
    assert policy.precipitant_drug == "bupropion"
    assert policy.object_drug == "vortioxetine"
    assert policy.target == "CYP2D6"

    aggregate = result.aggregate_concerns[0]
    assert aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_INCREASE
    assert aggregate.anchor == "vortioxetine"
    assert aggregate.targets == ("CYP2D6",)

    scored = result.scored_concerns[0]
    assert scored.policy_concern == POLICY_MECHANISTIC_CONCERN
    assert scored.precipitant_drug == "bupropion"
    assert scored.object_drug == "vortioxetine"
    assert scored.target == "CYP2D6"
    assert scored.confidence == "high"
    assert scored.severity == "unscored"

def test_run_mechanism_pipeline_returns_empty_stages_without_candidates():
    facts = Facts(
        drugs={
            "bupropion": Drug(
                id="bupropion",
                generic_name="bupropion",
                drug_class="NDRI antidepressant",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={
            "bupropion": [
                EnzymeRole(
                    enzyme_id="CYP2D6",
                    role="inhibitor",
                    strength="strong",
                )
            ],
        },
        transporter_roles={},
        pd_effects={},
    )

    result = run_mechanism_pipeline(["bupropion"], facts)

    assert len(result.effects) == 1
    assert result.candidates == ()
    assert result.arbitration_results == ()
    assert result.policy_results == ()
    assert result.aggregate_concerns == ()
    assert result.scored_concerns == ()
    
