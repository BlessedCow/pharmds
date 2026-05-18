import json

from core.mechanisms.pipeline import run_mechanism_pipeline
from core.mechanisms.pipeline_json import mechanism_pipeline_to_json_dict
from core.models import Drug, EnzymeRole, Facts, PDEffect


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
        "aggregate_severity_annotations",
        "aggregate_evidence_summaries",
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


def test_mechanism_pipeline_to_json_dict_includes_evidence_trace_metadata():
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

    pipeline = run_mechanism_pipeline(
        ["clarithromycin", "fluconazole"],
        facts,
    )
    payload = mechanism_pipeline_to_json_dict(pipeline)

    concern = next(
        concern
        for concern in payload["scored_concerns"]
        if concern["effect_id"] == "nausea"
    )
    trace = concern["metadata"]["evidence_trace"]

    assert trace["trace_type"] == "additive_pd_effect"
    assert trace["effect_id"] == "nausea"
    assert trace["drug_ids"] == ["clarithromycin", "fluconazole"]
    assert trace["overall_evidence_status"] == "complete"

    drug_traces = {
        drug_trace["drug_id"]: drug_trace
        for drug_trace in trace["drugs"]
    }

    assert set(drug_traces) == {"clarithromycin", "fluconazole"}
    assert drug_traces["clarithromycin"]["evidence_status"] == "present"
    assert drug_traces["fluconazole"]["evidence_status"] == "present"

    clarithromycin_claim = drug_traces["clarithromycin"]["claims"][0]
    fluconazole_claim = drug_traces["fluconazole"]["claims"][0]

    assert clarithromycin_claim["claim_id"] == (
        "claim_clarithromycin_pd_effect_nausea_001"
    )
    assert clarithromycin_claim["claim_type"] == "pd_effect"
    assert clarithromycin_claim["review"]["status"] == "approved"

    assert fluconazole_claim["claim_id"] == (
        "claim_fluconazole_pd_effect_nausea_001"
    )
    assert fluconazole_claim["claim_type"] == "pd_effect"
    assert fluconazole_claim["review"]["status"] == "approved"

    clarithromycin_evidence = clarithromycin_claim["evidence"][0]

    assert clarithromycin_evidence["confidence"] == "moderate"
    assert clarithromycin_evidence["source"] == {
        "source_id": "source_internal_curated_pd_effects_v1",
        "found": True,
        "title": "Internal curated pharmacodynamic effects dataset",
        "source_type": "internal_curated_entry",
        "publisher": "PharmDS",
        "url": None,
        "published_at": None,
        "accessed_at": None,
        "version": "1.0",
        "reliability_tier": "curated",
    }

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
        "aggregate_severity_annotations": [],
        "aggregate_evidence_summaries": [],
    }
    json.dumps(payload)