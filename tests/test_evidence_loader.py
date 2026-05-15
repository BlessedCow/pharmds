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
        == "claim_alprazolam_pd_effect_cns_depression_001"
    )