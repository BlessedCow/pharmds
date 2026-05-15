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
        "claim_alprazolam_pd_effect_cns_depression_001"
        in claim_ids_by_drug["alprazolam"]
    )
    assert (
        "claim_clonazepam_pd_effect_cns_depression_001"
        in claim_ids_by_drug["clonazepam"]
    )
    
