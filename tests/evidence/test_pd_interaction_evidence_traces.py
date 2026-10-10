import pytest

from core.evidence.pd_interaction_traces import (
    build_additive_pd_effect_evidence_trace,
    build_additive_pd_effect_evidence_traces,
)


def test_build_additive_pd_effect_evidence_trace_returns_complete_status():
    trace = build_additive_pd_effect_evidence_trace(
        ["clarithromycin", "fluconazole"],
        "nausea",
    )

    assert trace["trace_type"] == "additive_pd_effect"
    assert trace["effect_id"] == "nausea"
    assert trace["drug_ids"] == ["clarithromycin", "fluconazole"]
    assert trace["overall_evidence_status"] == "complete"

    assert len(trace["drugs"]) == 2

    statuses = {
        item["drug_id"]: item["evidence_status"]
        for item in trace["drugs"]
    }

    assert statuses == {
        "clarithromycin": "present",
        "fluconazole": "present",
    }


def test_build_additive_pd_effect_evidence_trace_includes_claims():
    trace = build_additive_pd_effect_evidence_trace(
        ["clarithromycin", "fluconazole"],
        "nausea",
    )

    claims_by_drug = {
        item["drug_id"]: item["claims"]
        for item in trace["drugs"]
    }

    clarithromycin_claim_ids = {
        claim["claim_id"]
        for claim in claims_by_drug["clarithromycin"]
    }
    fluconazole_claim_ids = {
        claim["claim_id"]
        for claim in claims_by_drug["fluconazole"]
    }

    assert (
        "claim_clarithromycin_pd_effect_nausea_001"
        in clarithromycin_claim_ids
    )
    assert (
        "claim_fluconazole_pd_effect_nausea_001"
        in fluconazole_claim_ids
    )


def test_build_additive_pd_effect_evidence_trace_returns_partial_status():
    trace = build_additive_pd_effect_evidence_trace(
        ["clarithromycin", "alprazolam"],
        "nausea",
    )

    assert trace["overall_evidence_status"] == "partial"

    statuses = {
        item["drug_id"]: item["evidence_status"]
        for item in trace["drugs"]
    }

    assert statuses["clarithromycin"] == "present"
    assert statuses["alprazolam"] == "missing"


def test_build_additive_pd_effect_evidence_trace_returns_missing_status():
    trace = build_additive_pd_effect_evidence_trace(
        ["alprazolam", "clonazepam"],
        "nausea",
    )

    assert trace["overall_evidence_status"] == "missing"

    statuses = {
        item["drug_id"]: item["evidence_status"]
        for item in trace["drugs"]
    }

    assert statuses == {
        "alprazolam": "missing",
        "clonazepam": "missing",
    }


def test_build_additive_pd_effect_evidence_traces_returns_one_trace_per_effect():
    traces = build_additive_pd_effect_evidence_traces(
        ["clarithromycin", "fluconazole"],
        ["nausea", "sedation"],
    )

    assert len(traces) == 2

    traces_by_effect = {
        trace["effect_id"]: trace
        for trace in traces
    }

    assert traces_by_effect["nausea"]["overall_evidence_status"] == "complete"
    assert traces_by_effect["sedation"]["overall_evidence_status"] == "missing"
    
def test_build_additive_pd_effect_evidence_trace_returns_complete_for_sedation():
    trace = build_additive_pd_effect_evidence_trace(
        ["alprazolam", "clonazepam"],
        "sedation",
    )

    assert trace["overall_evidence_status"] == "complete"

    statuses = {
        item["drug_id"]: item["evidence_status"]
        for item in trace["drugs"]
    }

    assert statuses == {
        "alprazolam": "present",
        "clonazepam": "present",
    }
    
def test_build_additive_pd_effect_evidence_trace_returns_complete_for_cns_depression():
    trace = build_additive_pd_effect_evidence_trace(
        ["alprazolam", "clonazepam"],
        "CNS_depression",
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    assert (
        "claim_alprazolam_pd_effect_CNS_depression_001"
        in claim_ids_by_drug["alprazolam"]
    )
    assert (
        "claim_clonazepam_pd_effect_CNS_depression_001"
        in claim_ids_by_drug["clonazepam"]
    )

def test_build_additive_pd_effect_evidence_trace_returns_complete_for_qt():
    trace = build_additive_pd_effect_evidence_trace(
        ["clarithromycin", "fluconazole"],
        "QT_prolongation",
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    assert (
        "claim_clarithromycin_pd_effect_QT_prolongation_001"
        in claim_ids_by_drug["clarithromycin"]
    )
    assert (
        "claim_fluconazole_pd_effect_QT_prolongation_001"
        in claim_ids_by_drug["fluconazole"]
    )
    
def test_build_additive_pd_effect_evidence_trace_returns_complete_for_serotonergic():
    trace = build_additive_pd_effect_evidence_trace(
        ["citalopram", "sertraline"],
        "serotonergic",
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    assert (
        "claim_citalopram_pd_effect_serotonergic_001"
        in claim_ids_by_drug["citalopram"]
    )
    assert (
        "claim_sertraline_pd_effect_serotonergic_001"
        in claim_ids_by_drug["sertraline"]
    )


def test_build_additive_pd_trace_returns_complete_for_serotonin_syndrome():
    trace = build_additive_pd_effect_evidence_trace(
        ["citalopram", "sertraline"],
        "serotonin_syndrome",
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    assert (
        "claim_citalopram_pd_effect_serotonin_syndrome_001"
        in claim_ids_by_drug["citalopram"]
    )
    assert (
        "claim_sertraline_pd_effect_serotonin_syndrome_001"
        in claim_ids_by_drug["sertraline"]
    )
    
def test_build_additive_pd_effect_evidence_trace_returns_complete_for_bleeding():
    trace = build_additive_pd_effect_evidence_trace(
        ["warfarin", "ibuprofen"],
        "bleeding",
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    assert (
        "claim_warfarin_pd_effect_bleeding_001"
        in claim_ids_by_drug["warfarin"]
    )
    assert (
        "claim_ibuprofen_pd_effect_bleeding_001"
        in claim_ids_by_drug["ibuprofen"]
    )
    

def test_build_additive_pd_effect_evidence_trace_returns_complete_for_seizure_risk():
    trace = build_additive_pd_effect_evidence_trace(
        ["bupropion", "ginkgo_biloba"],
        "seizure_risk",
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    assert (
        "claim_bupropion_pd_effect_seizure_risk_001"
        in claim_ids_by_drug["bupropion"]
    )
    assert (
        "claim_ginkgo_biloba_pd_effect_seizure_risk_001"
        in claim_ids_by_drug["ginkgo_biloba"]
    )
    
@pytest.mark.parametrize(
    ("drug_ids", "effect_id", "expected_claim_ids_by_drug"),
    [
        (
            ["vortioxetine", "varenicline"],
            "insomnia_risk",
            {
                "vortioxetine": {
                    "claim_vortioxetine_pd_effect_insomnia_risk_001",
                },
                "varenicline": {
                    "claim_varenicline_pd_effect_insomnia_risk_001",
                },
            },
        ),
        (
            ["vortioxetine", "varenicline"],
            "activation_agitation_risk",
            {
                "vortioxetine": {
                    "claim_vortioxetine_pd_effect_activation_agitation_risk_001",
                },
                "varenicline": {
                    "claim_varenicline_pd_effect_activation_agitation_risk_001",
                },
            },
        ),
        (
            ["hydroxyzine", "paroxetine"],
            "anticholinergic_effects",
            {
                "hydroxyzine": {
                    "claim_hydroxyzine_pd_effect_anticholinergic_effects_001",
                },
                "paroxetine": {
                    "claim_paroxetine_pd_effect_anticholinergic_effects_001",
                },
            },
        ),
        (
            ["trazodone", "clonidine"],
            "orthostatic_hypotension",
            {
                "trazodone": {
                    "claim_trazodone_pd_effect_orthostatic_hypotension_001",
                },
                "clonidine": {
                    "claim_clonidine_pd_effect_orthostatic_hypotension_001",
                },
            },
        ),
    ],
)
def test_build_additive_pd_effect_evidence_trace_returns_complete_for_expanded_batch(
    drug_ids,
    effect_id,
    expected_claim_ids_by_drug,
):
    trace = build_additive_pd_effect_evidence_trace(
        drug_ids,
        effect_id,
    )

    assert trace["overall_evidence_status"] == "complete"

    claim_ids_by_drug = {
        item["drug_id"]: {
            claim["claim_id"]
            for claim in item["claims"]
        }
        for item in trace["drugs"]
    }

    for drug_id, expected_claim_ids in expected_claim_ids_by_drug.items():
        assert expected_claim_ids <= claim_ids_by_drug[drug_id]
        
def test_additive_pd_effect_trace_includes_real_source_records():
    trace = build_additive_pd_effect_evidence_trace(
        ["clarithromycin", "fluconazole"],
        "QT_prolongation",
    )

    source_ids_by_drug = {
        item["drug_id"]: {
            evidence["source"]["source_id"]
            for claim in item["claims"]
            for evidence in claim["evidence"]
        }
        for item in trace["drugs"]
    }

    assert (
        "source_dailymed_clarithromycin_label"
        in source_ids_by_drug["clarithromycin"]
    )
    assert (
        "source_dailymed_fluconazole_label"
        in source_ids_by_drug["fluconazole"]
    )
    
    
