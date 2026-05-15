import json
from pathlib import Path

import pytest

from core.evidence.traces import (
    build_pd_effect_claim_trace,
    build_pd_effect_traces_for_drug,
    build_pd_effect_traces_for_drug_effect,
    build_source_trace,
    has_approved_active_pd_effect_evidence,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRUGS_PATH = PROJECT_ROOT / "data" / "curation" / "drugs.json"


def _ontology_pd_effect_pairs() -> set[tuple[str, str]]:
    raw = json.loads(DRUGS_PATH.read_text(encoding="utf-8"))

    pairs = set()

    for drug in raw["drugs"]:
        drug_id = drug["id"]

        for pd_effect in drug.get("pd_effects", []) or []:
            pairs.add((drug_id, pd_effect["effect_id"]))

    return pairs

def test_build_source_trace_returns_source_metadata():
    trace = build_source_trace("source_internal_curated_pd_effects_v1")

    assert trace == {
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

def test_build_source_trace_returns_real_drug_label_source():
    trace = build_source_trace("source_dailymed_clarithromycin_label")

    assert trace == {
        "source_id": "source_dailymed_clarithromycin_label",
        "found": True,
        "title": "Clarithromycin Prescribing Information",
        "source_type": "drug_label",
        "publisher": "DailyMed",
        "url": (
            "https://dailymed.nlm.nih.gov/dailymed/search.cfm?"
            "query=clarithromycin"
        ),
        "published_at": None,
        "accessed_at": "2026-05-15",
        "version": None,
        "reliability_tier": "authoritative",
    }
    

def test_build_source_trace_handles_missing_source():
    trace = build_source_trace("source_missing")

    assert trace == {
        "source_id": "source_missing",
        "found": False,
        "title": None,
        "source_type": None,
        "publisher": None,
        "url": None,
        "published_at": None,
        "accessed_at": None,
        "version": None,
        "reliability_tier": None,
    }


def test_build_pd_effect_claim_trace_returns_expected_shape():
    claim = {
        "claim_id": "claim_example_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "example_drug",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "nausea",
        },
        "evidence": [
            {
                "source_id": "source_internal_curated_pd_effects_v1",
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Example note.",
            }
        ],
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": None,
        },
        "claim_status": "active",
    }

    trace = build_pd_effect_claim_trace(claim)

    assert trace["claim_id"] == "claim_example_pd_effect_nausea_001"
    assert trace["claim_type"] == "pd_effect"
    assert trace["drug_id"] == "example_drug"
    assert trace["predicate"] == "has_pd_effect"
    assert trace["effect_id"] == "nausea"
    assert trace["claim_status"] == "active"
    assert trace["review"]["status"] == "approved"

    assert len(trace["evidence"]) == 1
    evidence = trace["evidence"][0]

    assert evidence["evidence_type"] == "internal_curated_entry"
    assert evidence["supports_claim"] is True
    assert evidence["confidence"] == "moderate"
    assert evidence["notes"] == "Example note."
    assert evidence["source"]["source_id"] == "source_internal_curated_pd_effects_v1"
    assert evidence["source"]["found"] is True


def test_build_pd_effect_traces_for_drug_effect_returns_matching_trace():
    traces = build_pd_effect_traces_for_drug_effect(
        "clarithromycin",
        "nausea",
    )

    assert len(traces) == 1

    trace = traces[0]

    assert trace["claim_id"] == "claim_clarithromycin_pd_effect_nausea_001"
    assert trace["drug_id"] == "clarithromycin"
    assert trace["effect_id"] == "nausea"
    assert trace["review"]["status"] == "approved"
    assert trace["claim_status"] == "active"

    assert trace["evidence"][0]["confidence"] == "moderate"
    assert (
        trace["evidence"][0]["source"]["source_id"]
        == "source_internal_curated_pd_effects_v1"
    )


def test_build_pd_effect_traces_for_drug_effect_returns_empty_for_mismatch():
    traces = build_pd_effect_traces_for_drug_effect(
        "clarithromycin",
        "sedation",
    )

    assert traces == []


def test_build_pd_effect_traces_for_drug_returns_matching_traces():
    traces = build_pd_effect_traces_for_drug("fluconazole")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_fluconazole_pd_effect_nausea_001" in claim_ids


def test_has_approved_active_pd_effect_evidence_returns_true_for_known_claim():
    result = has_approved_active_pd_effect_evidence(
        "fluconazole",
        "nausea",
    )

    assert result is True


def test_has_approved_active_pd_effect_evidence_returns_false_for_missing_claim():
    result = has_approved_active_pd_effect_evidence(
        "fluconazole",
        "sedation",
    )

    assert result is False
    
def test_build_pd_effect_traces_for_drug_returns_expanded_pd_claims():
    traces = build_pd_effect_traces_for_drug("alprazolam")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_alprazolam_pd_effect_sedation_001" in claim_ids
    assert "claim_alprazolam_pd_effect_CNS_depression_001" in claim_ids
    
def test_has_approved_active_pd_effect_evidence_returns_true_for_expanded_claim():
    result = has_approved_active_pd_effect_evidence(
        "clonazepam",
        "sedation",
    )

    assert result is True
    
def test_build_pd_effect_traces_for_drug_returns_qt_claim():
    traces = build_pd_effect_traces_for_drug("clarithromycin")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_clarithromycin_pd_effect_QT_prolongation_001" in claim_ids
    
def test_has_approved_active_pd_effect_evidence_returns_true_for_qt_claim():
    result = has_approved_active_pd_effect_evidence(
        "fluconazole",
        "QT_prolongation",
    )

    assert result is True
    
def test_build_pd_effect_traces_for_drug_returns_serotonergic_claims():
    traces = build_pd_effect_traces_for_drug("sertraline")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_sertraline_pd_effect_serotonergic_001" in claim_ids
    assert "claim_sertraline_pd_effect_serotonin_syndrome_001" in claim_ids


def test_has_approved_active_pd_effect_evidence_returns_true_for_serotonergic_claim():
    result = has_approved_active_pd_effect_evidence(
        "citalopram",
        "serotonergic",
    )

    assert result is True
    
def test_build_pd_effect_traces_for_drug_returns_bleeding_claim():
    traces = build_pd_effect_traces_for_drug("ibuprofen")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_ibuprofen_pd_effect_bleeding_001" in claim_ids


def test_has_approved_active_pd_effect_evidence_returns_true_for_bleeding_claim():
    result = has_approved_active_pd_effect_evidence(
        "warfarin",
        "bleeding",
    )

    assert result is True
    
def test_build_pd_effect_traces_for_drug_returns_seizure_risk_claim():
    traces = build_pd_effect_traces_for_drug("ginkgo_biloba")

    claim_ids = {trace["claim_id"] for trace in traces}

    assert "claim_ginkgo_biloba_pd_effect_seizure_risk_001" in claim_ids


def test_has_approved_active_pd_effect_evidence_returns_true_for_seizure_risk_claim():
    result = has_approved_active_pd_effect_evidence(
        "bupropion",
        "seizure_risk",
    )

    assert result is True
    
@pytest.mark.parametrize(
    ("drug_id", "expected_claim_ids"),
    [
        (
            "vortioxetine",
            {
                "claim_vortioxetine_pd_effect_insomnia_risk_001",
                "claim_vortioxetine_pd_effect_activation_agitation_risk_001",
            },
        ),
        (
            "varenicline",
            {
                "claim_varenicline_pd_effect_insomnia_risk_001",
                "claim_varenicline_pd_effect_activation_agitation_risk_001",
            },
        ),
        (
            "hydroxyzine",
            {
                "claim_hydroxyzine_pd_effect_anticholinergic_effects_001",
            },
        ),
        (
            "clonidine",
            {
                "claim_clonidine_pd_effect_orthostatic_hypotension_001",
            },
        ),
    ],
)
def test_build_pd_effect_traces_for_drug_returns_expanded_batch_claims(
    drug_id,
    expected_claim_ids,
):
    traces = build_pd_effect_traces_for_drug(drug_id)

    claim_ids = {
        trace["claim_id"]
        for trace in traces
    }

    assert expected_claim_ids <= claim_ids


@pytest.mark.parametrize(
    ("drug_id", "effect_id"),
    [
        ("vortioxetine", "insomnia_risk"),
        ("varenicline", "activation_agitation_risk"),
        ("paroxetine", "anticholinergic_effects"),
        ("clonidine", "orthostatic_hypotension"),
    ],
)
def test_has_approved_active_pd_effect_evidence_returns_true_for_expanded_batch(
    drug_id,
    effect_id,
):
    result = has_approved_active_pd_effect_evidence(
        drug_id,
        effect_id,
    )

    assert result is True
    
def test_all_curated_pd_effects_have_approved_active_evidence_traces():
    for drug_id, effect_id in _ontology_pd_effect_pairs():
        result = has_approved_active_pd_effect_evidence(
            drug_id,
            effect_id,
        )

        assert result is True
        
def test_selected_pd_effect_trace_includes_real_source_trace():
    traces = build_pd_effect_traces_for_drug_effect(
        "clarithromycin",
        "QT_prolongation",
    )

    assert len(traces) == 1

    evidence_items = traces[0]["evidence"]

    source_ids = {
        evidence["source"]["source_id"]
        for evidence in evidence_items
    }

    assert "source_internal_curated_pd_effects_v1" in source_ids
    assert "source_dailymed_clarithromycin_label" in source_ids
    

