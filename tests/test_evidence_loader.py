import json
from pathlib import Path

import pytest

from core.evidence.loader import (
    get_approved_active_pd_effect_claims,
    get_approved_active_pd_effect_claims_for_drug,
    get_approved_active_pd_effect_claims_for_drug_effect,
    get_pd_effect_claims_for_drug,
    get_pd_effect_claims_for_drug_effect,
    get_pd_effect_claims_for_effect,
    get_source_by_id,
    load_pd_effect_claims,
    load_sources,
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


def _claim_pd_effect_pairs() -> set[tuple[str, str]]:
    claims = get_approved_active_pd_effect_claims()

    return {
        (
            claim["subject"]["id"],
            claim["object"]["effect_id"],
        )
        for claim in claims
        if claim["claim_type"] == "pd_effect"
    }

def test_load_sources_returns_sources():
    sources = load_sources()

    assert sources
    assert isinstance(sources, list)
    assert sources[0]["source_id"] == "source_internal_curated_pd_effects_v1"


def test_load_pd_effect_claims_returns_claims():
    claims = load_pd_effect_claims()

    assert claims
    assert isinstance(claims, list)
    assert any(
        claim["claim_id"] == "claim_clarithromycin_pd_effect_nausea_001"
        for claim in claims
    )


def test_get_source_by_id_returns_matching_source():
    source = get_source_by_id("source_internal_curated_pd_effects_v1")

    assert source is not None
    assert source["title"] == "Internal curated pharmacodynamic effects dataset"

def test_load_sources_includes_real_drug_label_sources():
    sources = load_sources()

    source_ids = {
        source["source_id"]
        for source in sources
    }

    assert "source_dailymed_clarithromycin_label" in source_ids
    assert "source_dailymed_fluconazole_label" in source_ids


def test_get_source_by_id_returns_real_drug_label_source():
    source = get_source_by_id("source_dailymed_fluconazole_label")

    assert source is not None
    assert source["title"] == "Fluconazole Prescribing Information"
    assert source["source_type"] == "drug_label"
    assert source["publisher"] == "DailyMed"
    assert source["reliability_tier"] == "authoritative"
    assert source["accessed_at"] == "2026-05-15"
    

def test_get_source_by_id_returns_none_for_unknown_source():
    source = get_source_by_id("source_missing")

    assert source is None


def test_get_pd_effect_claims_for_drug_returns_matching_claims():
    claims = get_pd_effect_claims_for_drug("clarithromycin")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_clarithromycin_pd_effect_nausea_001" in claim_ids


def test_get_pd_effect_claims_for_drug_returns_empty_list_for_unknown_drug():
    claims = get_pd_effect_claims_for_drug("not_a_real_drug")

    assert claims == []


def test_get_pd_effect_claims_for_effect_returns_matching_claims():
    claims = get_pd_effect_claims_for_effect("nausea")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_clarithromycin_pd_effect_nausea_001" in claim_ids
    assert "claim_fluconazole_pd_effect_nausea_001" in claim_ids


def test_get_pd_effect_claims_for_drug_effect_returns_matching_claim():
    claims = get_pd_effect_claims_for_drug_effect(
        "clarithromycin",
        "nausea",
    )

    assert len(claims) == 1
    assert claims[0]["claim_id"] == "claim_clarithromycin_pd_effect_nausea_001"


def test_get_pd_effect_claims_for_drug_effect_returns_empty_list_for_mismatch():
    claims = get_pd_effect_claims_for_drug_effect(
        "clarithromycin",
        "sedation",
    )

    assert claims == []


def test_get_approved_active_pd_effect_claims_returns_only_approved_active_claims():
    claims = get_approved_active_pd_effect_claims()

    assert claims

    for claim in claims:
        assert claim["claim_type"] == "pd_effect"
        assert claim["claim_status"] == "active"
        assert claim["review"]["status"] == "approved"


def test_get_approved_active_pd_effect_claims_for_drug_returns_matching_claims():
    claims = get_approved_active_pd_effect_claims_for_drug("fluconazole")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_fluconazole_pd_effect_nausea_001" in claim_ids


def test_get_approved_active_pd_effect_claims_for_drug_effect_returns_match():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "fluconazole",
        "nausea",
    )

    assert len(claims) == 1
    assert claims[0]["claim_id"] == "claim_fluconazole_pd_effect_nausea_001"
    
def test_get_pd_effect_claims_for_effect_returns_sedation_claims():
    claims = get_pd_effect_claims_for_effect("sedation")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_alprazolam_pd_effect_sedation_001" in claim_ids
    assert "claim_clonazepam_pd_effect_sedation_001" in claim_ids
    
def test_get_approved_active_pd_effect_claims_for_drug_effect_returns_cns_match():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "alprazolam",
        "CNS_depression",
    )

    assert len(claims) == 1
    assert (
        claims[0]["claim_id"]
        == "claim_alprazolam_pd_effect_CNS_depression_001"
    )

def test_get_pd_effect_claims_for_effect_returns_qt_claims():
    claims = get_pd_effect_claims_for_effect("QT_prolongation")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_clarithromycin_pd_effect_QT_prolongation_001" in claim_ids
    assert "claim_fluconazole_pd_effect_QT_prolongation_001" in claim_ids
    
def test_get_approved_active_pd_effect_claims_for_drug_effect_returns_qt_match():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "fluconazole",
        "QT_prolongation",
    )

    assert len(claims) == 1
    assert (
        claims[0]["claim_id"]
        == "claim_fluconazole_pd_effect_QT_prolongation_001"
    )
    
def test_get_pd_effect_claims_for_effect_returns_serotonergic_claims():
    claims = get_pd_effect_claims_for_effect("serotonergic")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_citalopram_pd_effect_serotonergic_001" in claim_ids
    assert "claim_sertraline_pd_effect_serotonergic_001" in claim_ids


def test_get_approved_active_pd_effect_claims_returns_serotonin_syndrome_match():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "citalopram",
        "serotonin_syndrome",
    )

    assert len(claims) == 1
    assert (
        claims[0]["claim_id"]
        == "claim_citalopram_pd_effect_serotonin_syndrome_001"
    )
    
def test_get_pd_effect_claims_for_effect_returns_bleeding_claims():
    claims = get_pd_effect_claims_for_effect("bleeding")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_warfarin_pd_effect_bleeding_001" in claim_ids
    assert "claim_ibuprofen_pd_effect_bleeding_001" in claim_ids


def test_get_approved_active_pd_effect_claims_for_drug_effect_returns_bleeding_match():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "warfarin",
        "bleeding",
    )

    assert len(claims) == 1
    assert claims[0]["claim_id"] == "claim_warfarin_pd_effect_bleeding_001"
    
def test_get_pd_effect_claims_for_effect_returns_seizure_risk_claims():
    claims = get_pd_effect_claims_for_effect("seizure_risk")

    claim_ids = {claim["claim_id"] for claim in claims}

    assert "claim_bupropion_pd_effect_seizure_risk_001" in claim_ids
    assert "claim_ginkgo_biloba_pd_effect_seizure_risk_001" in claim_ids


def test_get_approved_active_pd_effect_claims_returns_seizure_risk_match():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "bupropion",
        "seizure_risk",
    )

    assert len(claims) == 1
    assert claims[0]["claim_id"] == (
        "claim_bupropion_pd_effect_seizure_risk_001"
    )
    
@pytest.mark.parametrize(
    ("effect_id", "expected_claim_ids"),
    [
        (
            "insomnia_risk",
            {
                "claim_vortioxetine_pd_effect_insomnia_risk_001",
                "claim_varenicline_pd_effect_insomnia_risk_001",
            },
        ),
        (
            "activation_agitation_risk",
            {
                "claim_vortioxetine_pd_effect_activation_agitation_risk_001",
                "claim_varenicline_pd_effect_activation_agitation_risk_001",
            },
        ),
        (
            "anticholinergic_effects",
            {
                "claim_hydroxyzine_pd_effect_anticholinergic_effects_001",
                "claim_paroxetine_pd_effect_anticholinergic_effects_001",
            },
        ),
        (
            "orthostatic_hypotension",
            {
                "claim_trazodone_pd_effect_orthostatic_hypotension_001",
                "claim_clonidine_pd_effect_orthostatic_hypotension_001",
            },
        ),
    ],
)
def test_get_pd_effect_claims_for_effect_returns_expanded_batch_claims(
    effect_id,
    expected_claim_ids,
):
    claims = get_pd_effect_claims_for_effect(effect_id)

    claim_ids = {
        claim["claim_id"]
        for claim in claims
    }

    assert expected_claim_ids <= claim_ids


@pytest.mark.parametrize(
    ("drug_id", "effect_id", "expected_claim_id"),
    [
        (
            "vortioxetine",
            "insomnia_risk",
            "claim_vortioxetine_pd_effect_insomnia_risk_001",
        ),
        (
            "varenicline",
            "activation_agitation_risk",
            "claim_varenicline_pd_effect_activation_agitation_risk_001",
        ),
        (
            "hydroxyzine",
            "anticholinergic_effects",
            "claim_hydroxyzine_pd_effect_anticholinergic_effects_001",
        ),
        (
            "trazodone",
            "orthostatic_hypotension",
            "claim_trazodone_pd_effect_orthostatic_hypotension_001",
        ),
    ],
)
def test_get_approved_active_pd_effect_claims_returns_expanded_batch_match(
    drug_id,
    effect_id,
    expected_claim_id,
):
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        drug_id,
        effect_id,
    )

    assert len(claims) == 1
    assert claims[0]["claim_id"] == expected_claim_id
    
def test_approved_active_pd_effect_claims_cover_curated_ontology():
    missing_pairs = _ontology_pd_effect_pairs() - _claim_pd_effect_pairs()

    assert missing_pairs == set()


def test_pd_effect_claim_ids_are_unique():
    claims = load_pd_effect_claims()
    claim_ids = [
        claim["claim_id"]
        for claim in claims
    ]

    assert len(claim_ids) == len(set(claim_ids))


def test_pd_effect_claim_ids_match_canonical_pattern():
    claims = load_pd_effect_claims()

    for claim in claims:
        drug_id = claim["subject"]["id"]
        effect_id = claim["object"]["effect_id"]
        expected_claim_id = f"claim_{drug_id}_pd_effect_{effect_id}_001"

        assert claim["claim_id"] == expected_claim_id
        
def test_selected_pd_effect_claims_include_real_source_evidence():
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        "fluconazole",
        "QT_prolongation",
    )

    assert len(claims) == 1

    source_ids = {
        evidence["source_id"]
        for evidence in claims[0]["evidence"]
    }

    assert "source_internal_curated_pd_effects_v1" in source_ids
    assert "source_dailymed_fluconazole_label" in source_ids
    
