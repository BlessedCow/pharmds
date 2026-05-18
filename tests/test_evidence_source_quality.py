from core.evidence.source_quality import (
    build_evidence_source_quality_report,
    collect_claim_source_ids,
    find_claims_with_missing_sources,
    find_sources_with_missing_metadata,
    find_unused_sources,
)


def _source(
    source_id,
    *,
    source_type="internal_curation",
    reliability_tier="curated",
    url=None,
    published_at=None,
    accessed_at=None,
):
    return {
        "source_id": source_id,
        "title": f"Title for {source_id}",
        "source_type": source_type,
        "publisher": "PharmDS",
        "url": url,
        "published_at": published_at,
        "accessed_at": accessed_at,
        "version": None,
        "reliability_tier": reliability_tier,
    }


def _claim(claim_id, source_ids):
    return {
        "claim_id": claim_id,
        "claim_type": "pd_effect",
        "evidence": [
            {
                "source_id": source_id,
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Test evidence.",
            }
            for source_id in source_ids
        ],
    }


def test_collect_claim_source_ids_returns_unique_source_ids():
    claims = [
        _claim("claim_a_001", ["source_a", "source_b"]),
        _claim("claim_b_001", ["source_a"]),
    ]

    assert collect_claim_source_ids(claims) == {
        "source_a",
        "source_b",
    }


def test_find_claims_with_missing_sources_reports_missing_references():
    claims = [
        _claim("claim_a_001", ["source_a", "source_missing"]),
    ]
    sources = [
        _source("source_a"),
    ]

    assert find_claims_with_missing_sources(claims, sources) == [
        {
            "claim_id": "claim_a_001",
            "source_id": "source_missing",
        }
    ]


def test_find_unused_sources_returns_sources_not_referenced_by_claims():
    claims = [
        _claim("claim_a_001", ["source_a"]),
    ]
    sources = [
        _source("source_a"),
        _source("source_unused"),
    ]

    assert find_unused_sources(claims, sources) == [
        _source("source_unused"),
    ]


def test_find_sources_with_missing_metadata_reports_recommended_fields():
    sources = [
        _source(
            "source_a",
            url="https://example.com",
            published_at="2026-05-13",
            accessed_at="2026-05-13",
        ),
        _source("source_b"),
    ]

    assert find_sources_with_missing_metadata(sources) == [
        {
            "source_id": "source_b",
            "missing_fields": [
                "url",
                "published_at",
                "accessed_at",
            ],
        }
    ]


def test_build_evidence_source_quality_report_returns_counts():
    claims = [
        _claim("claim_a_001", ["source_a"]),
        _claim("claim_b_001", ["source_missing"]),
    ]
    sources = [
        _source(
            "source_a",
            url="https://example.com",
            published_at="2026-05-13",
            accessed_at="2026-05-13",
        ),
        _source("source_unused", source_type="drug_label"),
    ]

    report = build_evidence_source_quality_report(
        claims,
        sources,
    )

    assert report["report_type"] == "evidence_source_quality_report"
    assert report["total_sources"] == 2
    assert report["total_claims"] == 2
    assert report["referenced_source_count"] == 2
    assert report["unused_source_count"] == 1
    assert report["missing_source_reference_count"] == 1
    assert report["sources_missing_metadata_count"] == 1
    assert report["source_type_counts"] == {
        "drug_label": 1,
        "internal_curation": 1,
    }
    assert report["reliability_tier_counts"] == {
        "curated": 2,
    }