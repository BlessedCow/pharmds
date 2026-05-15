from core.evidence.formatting import (
    format_claim_trace,
    format_evidence_item_trace,
    format_evidence_trace,
    format_source_trace,
)


def test_format_source_trace_returns_readable_source_summary():
    source = {
        "source_id": "source_internal_curated_pd_effects_v1",
        "found": True,
        "title": "Internal curated pharmacodynamic effects dataset",
        "source_type": "internal_curated_entry",
        "publisher": "PharmDS",
        "url": None,
        "reliability_tier": "curated",
    }

    assert format_source_trace(source) == (
        "Internal curated pharmacodynamic effects dataset "
        "(PharmDS, curated)"
    )


def test_format_source_trace_handles_missing_source():
    source = {
        "source_id": "source_missing",
        "found": False,
        "title": None,
        "source_type": None,
        "publisher": None,
        "url": None,
        "reliability_tier": None,
    }

    assert format_source_trace(source) == (
        "source_missing (source not found)"
    )


def test_format_evidence_item_trace_returns_readable_summary():
    evidence = {
        "source": {
            "source_id": "source_internal_curated_pd_effects_v1",
            "found": True,
            "title": "Internal curated pharmacodynamic effects dataset",
            "source_type": "internal_curated_entry",
            "publisher": "PharmDS",
            "url": None,
            "reliability_tier": "curated",
        },
        "evidence_type": "internal_curated_entry",
        "supports_claim": True,
        "confidence": "moderate",
        "notes": "Known nausea effect in curated data.",
    }

    assert format_evidence_item_trace(evidence) == (
        "Internal curated pharmacodynamic effects dataset "
        "(PharmDS, curated); "
        "evidence_type=internal_curated_entry; "
        "supports_claim=true; confidence=moderate"
    )


def test_format_claim_trace_returns_readable_summary():
    claim = {
        "claim_id": "claim_fluconazole_pd_effect_nausea_001",
        "claim_type": "pd_effect",
        "drug_id": "fluconazole",
        "predicate": "has_pd_effect",
        "effect_id": "nausea",
        "claim_status": "active",
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": None,
        },
        "evidence": [
            {
                "source": {
                    "source_id": "source_internal_curated_pd_effects_v1",
                    "found": True,
                    "title": "Internal curated pharmacodynamic effects dataset",
                    "source_type": "internal_curated_entry",
                    "publisher": "PharmDS",
                    "url": None,
                    "reliability_tier": "curated",
                },
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Known nausea effect in curated data.",
            }
        ],
    }

    assert format_claim_trace(claim) == (
        "fluconazole -> nausea: pd_effect; "
        "claim_status=active; review_status=approved; "
        "evidence_support_status=unknown; "
        "evidence=Internal curated pharmacodynamic effects dataset "
        "(PharmDS, curated); "
        "evidence_type=internal_curated_entry; "
        "supports_claim=true; confidence=moderate"
    )


def test_format_claim_trace_handles_claim_without_evidence():
    claim = {
        "claim_id": "claim_example",
        "claim_type": "pd_effect",
        "drug_id": "example_drug",
        "predicate": "has_pd_effect",
        "effect_id": "nausea",
        "claim_status": "active",
        "review": {
            "status": "approved",
        },
        "evidence": [],
    }

    assert format_claim_trace(claim) == (
        "example_drug -> nausea: pd_effect; "
        "claim_status=active; review_status=approved; "
        "evidence_support_status=unknown; evidence=none"
    )
    
    
def test_format_source_trace_includes_accessed_at_when_present():
    source = {
        "source_id": "source_dailymed_fluconazole_label",
        "found": True,
        "title": "Fluconazole Prescribing Information",
        "source_type": "drug_label",
        "publisher": "DailyMed",
        "url": "https://example.com/fluconazole",
        "published_at": None,
        "accessed_at": "2026-05-15",
        "version": None,
        "reliability_tier": "authoritative",
    }

    assert format_source_trace(source) == (
        "Fluconazole Prescribing Information "
        "(DailyMed, authoritative; accessed 2026-05-15)"
    )
    

def test_format_evidence_trace_returns_readable_lines():
    trace = {
        "trace_type": "additive_pd_effect",
        "effect_id": "nausea",
        "drug_ids": ["clarithromycin", "fluconazole"],
        "overall_evidence_status": "complete",
        "drugs": [
            {
                "drug_id": "clarithromycin",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "claim_id": (
                            "claim_clarithromycin_pd_effect_nausea_001"
                        ),
                        "claim_type": "pd_effect",
                        "drug_id": "clarithromycin",
                        "predicate": "has_pd_effect",
                        "effect_id": "nausea",
                        "claim_status": "active",
                        "review": {
                            "status": "approved",
                            "reviewed_by": "maintainer",
                            "reviewed_at": None,
                        },
                        "evidence": [
                            {
                                "source": {
                                    "source_id": (
                                        "source_internal_curated_pd_effects_v1"
                                    ),
                                    "found": True,
                                    "title": (
                                        "Internal curated pharmacodynamic "
                                        "effects dataset"
                                    ),
                                    "source_type": "internal_curated_entry",
                                    "publisher": "PharmDS",
                                    "url": None,
                                    "reliability_tier": "curated",
                                },
                                "evidence_type": "internal_curated_entry",
                                "supports_claim": True,
                                "confidence": "moderate",
                                "notes": "Known nausea effect.",
                            }
                        ],
                    }
                ],
            },
            {
                "drug_id": "fluconazole",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [],
            },
        ],
    }

    assert format_evidence_trace(trace) == [
        "Evidence status for nausea: complete",
        (
            "clarithromycin evidence_status=present; "
            "clarithromycin -> nausea: pd_effect; "
            "claim_status=active; review_status=approved; "
            "evidence_support_status=unknown; "
            "evidence=Internal curated pharmacodynamic effects dataset "
            "(PharmDS, curated); "
            "evidence_type=internal_curated_entry; "
            "supports_claim=true; confidence=moderate"
        ),
        (
            "fluconazole -> nausea: evidence_status=present; "
            "claims=none"
        ),
    ]