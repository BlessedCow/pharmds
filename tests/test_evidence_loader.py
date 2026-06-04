import json
from pathlib import Path

import pytest

from core.evidence.loader import (
    build_source_index,
    get_approved_active_pd_effect_claims,
    get_approved_active_pd_effect_claims_for_drug,
    get_approved_active_pd_effect_claims_for_drug_effect,
    get_pd_effect_claims_for_drug,
    get_pd_effect_claims_for_drug_effect,
    get_pd_effect_claims_for_effect,
    get_source_by_id,
    load_curated_drug_ids,
    load_curated_pd_effect_ids,
    load_pd_effect_claims,
    load_source_index,
    load_sources,
    validate_claim_domain_references,
    validate_claim_records,
    validate_claim_source_references,
    validate_evidence_source_registry,
    validate_source_records,
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

def test_load_pd_effect_claims_validates_current_claim_data():
    claims = load_pd_effect_claims()

    assert claims
    
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

def test_build_source_index_returns_source_id_keyed_lookup():
    sources = [
        _source_record("source_one"),
        _source_record("source_two"),
    ]

    source_index = build_source_index(sources)

    assert set(source_index) == {"source_one", "source_two"}
    assert source_index["source_one"]["source_id"] == "source_one"
    assert source_index["source_two"]["source_id"] == "source_two"


def test_load_source_index_returns_real_source_lookup():
    source_index = load_source_index()

    assert "source_internal_curated_pd_effects_v1" in source_index
    assert (
        source_index["source_internal_curated_pd_effects_v1"]["title"]
        == "Internal curated pharmacodynamic effects dataset"
    )

def test_load_curated_drug_ids_returns_known_drugs():
    drug_ids = load_curated_drug_ids()

    assert "amitriptyline" in drug_ids
    assert "hydroxyzine" in drug_ids


def test_load_curated_pd_effect_ids_returns_known_effects():
    effect_ids = load_curated_pd_effect_ids()

    assert "h1_antagonism" in effect_ids
    assert "sedation" in effect_ids


def test_validate_claim_domain_references_accepts_current_claims():
    validate_claim_domain_references(
        load_pd_effect_claims(),
        known_drug_ids=load_curated_drug_ids(),
        known_effect_ids=load_curated_pd_effect_ids(),
    )


def test_validate_claim_domain_references_rejects_unknown_drug_id():
    claims = [
        _claim_record(
            "claim_unknown_drug",
            subject={
                "entity_type": "drug",
                "id": "not_a_real_drug",
            },
        ),
    ]

    with pytest.raises(ValueError, match="unknown drug_id: not_a_real_drug"):
        validate_claim_domain_references(
            claims,
            known_drug_ids={"test_drug"},
            known_effect_ids={"sedation"},
        )


def test_validate_claim_domain_references_rejects_unknown_effect_id():
    claims = [
        _claim_record(
            "claim_unknown_effect",
            object={
                "effect_id": "not_a_real_effect",
            },
        ),
    ]

    with pytest.raises(ValueError, match="unknown effect_id: not_a_real_effect"):
        validate_claim_domain_references(
            claims,
            known_drug_ids={"test_drug"},
            known_effect_ids={"sedation"},
        )

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

def _claim_record(claim_id: str, **overrides):
    claim = {
        "claim_id": claim_id,
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "test_drug",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "sedation",
        },
        "evidence": [
            {
                "source_id": "source_known",
                "evidence_type": "drug_label",
                "supports_claim": True,
                "confidence": "high",
                "notes": "Test evidence.",
            }
        ],
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": "2026-05-26",
        },
        "claim_status": "active",
        "contributor": {
            "id": "project_maintainer",
            "role": "maintainer",
            "submitted_at": "2026-05-26",
        },
    }
    claim.update(overrides)

    return claim

def _source_record(source_id: str, **overrides):
    source = {
        "source_id": source_id,
        "title": f"Title for {source_id}",
        "source_type": "drug_label",
        "publisher": "DailyMed",
        "url": "https://example.com/source",
        "published_at": None,
        "accessed_at": "2026-05-26",
        "version": None,
        "reliability_tier": "authoritative",
    }
    source.update(overrides)

    return source


def test_validate_source_records_rejects_duplicate_source_ids():
    sources = [
        _source_record("source_duplicate"),
        _source_record("source_duplicate"),
    ]

    with pytest.raises(ValueError, match="Duplicate evidence source_id"):
        validate_source_records(sources)


def test_validate_source_records_rejects_missing_required_fields():
    source = _source_record("source_missing_title")
    del source["title"]

    with pytest.raises(ValueError, match="missing required fields: title"):
        validate_source_records([source])


def test_validate_source_records_rejects_unknown_source_type():
    sources = [
        _source_record("source_bad_type", source_type="blog_post"),
    ]

    with pytest.raises(ValueError, match="unknown source_type: blog_post"):
        validate_source_records(sources)


def test_validate_source_records_rejects_unknown_reliability_tier():
    sources = [
        _source_record("source_bad_tier", reliability_tier="excellent"),
    ]

    with pytest.raises(ValueError, match="unknown reliability_tier: excellent"):
        validate_source_records(sources)

def test_validate_evidence_source_registry_accepts_current_data():
    validate_evidence_source_registry()

def test_validate_claim_records_accepts_current_claims():
    validate_claim_records(load_pd_effect_claims())


def test_validate_claim_records_rejects_missing_required_fields():
    claim = _claim_record("claim_missing_subject")
    del claim["subject"]

    with pytest.raises(ValueError, match="missing required fields: subject"):
        validate_claim_records([claim])


def test_validate_claim_records_rejects_duplicate_claim_ids():
    claims = [
        _claim_record("claim_duplicate"),
        _claim_record("claim_duplicate"),
    ]

    with pytest.raises(ValueError, match="Duplicate evidence claim_id"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_blank_claim_id():
    claims = [
        _claim_record(""),
    ]

    with pytest.raises(ValueError, match="must include non-empty 'claim_id'"):
        validate_claim_records(claims)

def test_validate_claim_records_rejects_unknown_claim_type():
    claims = [
        _claim_record("claim_bad_type", claim_type="pk_effect"),
    ]

    with pytest.raises(ValueError, match="unknown claim_type: pk_effect"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_unknown_predicate():
    claims = [
        _claim_record("claim_bad_predicate", predicate="causes_effect"),
    ]

    with pytest.raises(ValueError, match="unknown predicate: causes_effect"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_non_object_subject():
    claims = [
        _claim_record("claim_bad_subject", subject="drug"),
    ]

    with pytest.raises(ValueError, match="subject must be an object"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_unknown_subject_entity_type():
    claims = [
        _claim_record(
            "claim_bad_subject_entity",
            subject={
                "entity_type": "food",
                "id": "grapefruit",
            },
        ),
    ]

    with pytest.raises(ValueError, match="unknown subject entity_type: food"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_blank_effect_id():
    claims = [
        _claim_record(
            "claim_blank_effect",
            object={
                "effect_id": "",
            },
        ),
    ]

    with pytest.raises(ValueError, match="must include non-empty 'effect_id'"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_empty_evidence_list():
    claims = [
        _claim_record("claim_empty_evidence", evidence=[]),
    ]

    with pytest.raises(ValueError, match="evidence must be a non-empty list"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_non_boolean_supports_claim():
    claims = [
        _claim_record(
            "claim_bad_supports_claim",
            evidence=[
                {
                    "source_id": "source_known",
                    "evidence_type": "drug_label",
                    "supports_claim": "yes",
                    "confidence": "high",
                    "notes": "Test evidence.",
                }
            ],
        ),
    ]

    with pytest.raises(ValueError, match="supports_claim must be a boolean"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_unknown_evidence_type():
    claims = [
        _claim_record(
            "claim_bad_evidence_type",
            evidence=[
                {
                    "source_id": "source_known",
                    "evidence_type": "blog_post",
                    "supports_claim": True,
                    "confidence": "high",
                    "notes": "Test evidence.",
                }
            ],
        ),
    ]

    with pytest.raises(ValueError, match="unknown evidence_type: blog_post"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_unknown_confidence():
    claims = [
        _claim_record(
            "claim_bad_confidence",
            evidence=[
                {
                    "source_id": "source_known",
                    "evidence_type": "drug_label",
                    "supports_claim": True,
                    "confidence": "certain",
                    "notes": "Test evidence.",
                }
            ],
        ),
    ]

    with pytest.raises(ValueError, match="unknown confidence: certain"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_unknown_review_status():
    claims = [
        _claim_record(
            "claim_bad_review_status",
            review={
                "status": "pending",
                "reviewed_by": "maintainer",
                "reviewed_at": "2026-05-26",
            },
        ),
    ]

    with pytest.raises(ValueError, match="unknown review status: pending"):
        validate_claim_records(claims)


def test_validate_claim_records_rejects_non_object_contributor():
    claims = [
        _claim_record("claim_bad_contributor", contributor="maintainer"),
    ]

    with pytest.raises(ValueError, match="contributor must be an object"):
        validate_claim_records(claims)

def test_validate_claim_source_references_rejects_unknown_source_id():
    claims = [
        {
            "claim_id": "claim_test_drug_pd_effect_sedation_001",
            "evidence": [
                {
                    "source_id": "source_missing",
                }
            ],
        }
    ]
    sources = [
        _source_record("source_known"),
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Evidence claim claim_test_drug_pd_effect_sedation_001 "
            "references unknown source_id: source_missing"
        ),
    ):
        validate_claim_source_references(claims, sources)
        
