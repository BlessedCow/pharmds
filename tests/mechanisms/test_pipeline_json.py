import json

from core.mechanisms.pipeline import run_mechanism_pipeline
from core.mechanisms.pipeline_json import mechanism_pipeline_to_json_dict
from core.models import Drug, EnzymeRole, Facts


def test_mechanism_pipeline_to_json_dict_serializes_all_stages():
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

    pipeline = run_mechanism_pipeline(
        ["bupropion", "vortioxetine"],
        facts,
    )
    payload = mechanism_pipeline_to_json_dict(pipeline)

    assert set(payload) == {
        "effects",
        "candidates",
        "arbitration_results",
        "policy_results",
        "scored_concerns",
        "severity_annotations",
        "aggregate_concerns",
    }

    assert payload["effects"][0]["source_drug"] == "bupropion"
    assert payload["candidates"][0]["candidate_type"] == (
        "ENZYME_INHIBITION_EXPOSURE"
    )
    assert payload["arbitration_results"][0]["concern"] == "exposure_increase"
    assert payload["policy_results"][0]["policy_concern"] == (
        "mechanistic_concern"
    )
    assert payload["scored_concerns"][0]["confidence"] == "high"
    assert payload["scored_concerns"][0]["severity"] == "unscored"
    assert payload["aggregate_concerns"][0]["aggregate_type"] == (
        "object_exposure_increase_cluster"
    )
    assert payload["severity_annotations"][0]["preliminary_severity"] == (
        "informational"
    )
    assert payload["severity_annotations"][0]["severity_reason"] == (
        "Single high-confidence mechanistic concern."
    )
    assert payload["severity_annotations"][0]["scored"]["confidence"] == "high"
    json.dumps(payload)


def test_mechanism_pipeline_to_json_dict_serializes_empty_stages():
    facts = Facts(
        drugs={
            "bupropion": Drug(
                id="bupropion",
                generic_name="bupropion",
                drug_class="NDRI antidepressant",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={},
        transporter_roles={},
        pd_effects={},
    )

    pipeline = run_mechanism_pipeline(["bupropion"], facts)
    payload = mechanism_pipeline_to_json_dict(pipeline)

    assert payload == {
        "effects": [],
        "candidates": [],
        "arbitration_results": [],
        "policy_results": [],
        "scored_concerns": [],
        "severity_annotations": [],
        "aggregate_concerns": [],
    }
    json.dumps(payload)
