from core.evidence.gating import (
    EVIDENCE_MODE_MODERATE,
    EVIDENCE_MODE_SUPPORTED,
)
from core.mechanisms.aggregation import AGGREGATE_OBJECT_EXPOSURE_INCREASE
from core.mechanisms.arbitration import CONCERN_EXPOSURE_INCREASE
from core.mechanisms.candidates import CANDIDATE_ENZYME_INHIBITION
from core.mechanisms.pipeline import run_mechanism_pipeline
from core.mechanisms.policy import POLICY_MECHANISTIC_CONCERN
from core.mechanisms.registry import (
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_SUBSTRATE,
)
from core.mechanisms.severity import PRELIMINARY_SEVERITY_INFORMATIONAL
from core.models import Drug, EnzymeRole, Facts, PDEffect


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
    assert len(result.severity_annotations) == 1

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
    
    severity = result.severity_annotations[0]
    assert severity.scored == scored
    assert severity.preliminary_severity == PRELIMINARY_SEVERITY_INFORMATIONAL
    assert severity.severity_reason == (
        "Single high-confidence mechanistic concern."
    )
def test_run_mechanism_pipeline_preserves_evidence_gated_compatibility(
    monkeypatch,
):
    seen = {}

    def fake_filter(facts, *, mode):
        seen["mode"] = mode
        return facts

    monkeypatch.setattr(
        "core.mechanisms.pipeline."
        "filter_facts_to_evidence_backed_pd_effects",
        fake_filter,
    )

    facts = Facts()
    run_mechanism_pipeline(
        [],
        facts,
        evidence_gated=True,
    )

    assert seen["mode"] == EVIDENCE_MODE_SUPPORTED


def test_run_mechanism_pipeline_accepts_evidence_mode(monkeypatch):
    seen = {}

    def fake_filter(facts, *, mode):
        seen["mode"] = mode
        return facts

    monkeypatch.setattr(
        "core.mechanisms.pipeline."
        "filter_facts_to_evidence_backed_pd_effects",
        fake_filter,
    )

    facts = Facts()
    run_mechanism_pipeline(
        [],
        facts,
        evidence_mode=EVIDENCE_MODE_MODERATE,
    )

    assert seen["mode"] == EVIDENCE_MODE_MODERATE
    
    
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
    
def test_run_mechanism_pipeline_keeps_default_behavior_without_evidence_gating():
    facts = Facts(
        drugs={
            "test_drug_a": Drug(
                id="test_drug_a",
                generic_name="Test Drug A",
                drug_class="test",
                therapeutic_index="moderate",
            ),
            "test_drug_b": Drug(
                id="test_drug_b",
                generic_name="Test Drug B",
                drug_class="test",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={},
        transporter_roles={},
        pd_effects={
            "test_drug_a": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                )
            ],
            "test_drug_b": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                )
            ],
        },
    )

    result = run_mechanism_pipeline(
        ["test_drug_a", "test_drug_b"],
        facts,
    )

    assert len(result.effects) == 2
    assert len(result.candidates) == 1
    assert len(result.arbitration_results) == 1
    assert len(result.policy_results) == 1
    assert len(result.scored_concerns) == 1


def test_run_mechanism_pipeline_filters_unsupported_pd_effects_when_evidence_gated():
    facts = Facts(
        drugs={
            "test_drug_a": Drug(
                id="test_drug_a",
                generic_name="Test Drug A",
                drug_class="test",
                therapeutic_index="moderate",
            ),
            "test_drug_b": Drug(
                id="test_drug_b",
                generic_name="Test Drug B",
                drug_class="test",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={},
        transporter_roles={},
        pd_effects={
            "test_drug_a": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                )
            ],
            "test_drug_b": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                )
            ],
        },
    )

    result = run_mechanism_pipeline(
        ["test_drug_a", "test_drug_b"],
        facts,
        evidence_gated=True,
    )

    assert result.effects == ()
    assert result.candidates == ()
    assert result.arbitration_results == ()
    assert result.policy_results == ()
    assert result.scored_concerns == ()
    assert result.severity_annotations == ()
    assert result.aggregate_concerns == ()


def test_run_mechanism_pipeline_keeps_supported_pd_effects_when_evidence_gated():
    facts = Facts(
        drugs={
            "clarithromycin": Drug(
                id="clarithromycin",
                generic_name="clarithromycin",
                drug_class="macrolide antibiotic",
                therapeutic_index="moderate",
            ),
            "fluconazole": Drug(
                id="fluconazole",
                generic_name="fluconazole",
                drug_class="azole antifungal",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={},
        transporter_roles={},
        pd_effects={
            "clarithromycin": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                )
            ],
            "fluconazole": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                )
            ],
        },
    )

    result = run_mechanism_pipeline(
        ["clarithromycin", "fluconazole"],
        facts,
        evidence_gated=True,
    )

    assert len(result.effects) == 2
    assert len(result.candidates) == 1
    assert len(result.arbitration_results) == 1
    assert len(result.policy_results) == 1
    assert len(result.scored_concerns) == 1

    scored = result.scored_concerns[0]

    assert scored.effect_id == "nausea"
    assert scored.metadata["evidence_trace"]["overall_evidence_status"] == (
        "complete"
    )