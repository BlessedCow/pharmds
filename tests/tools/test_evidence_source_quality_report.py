from tools.evidence_source_quality_report import _format_report_text


def _report():
    return {
        "report_type": "evidence_source_quality_report",
        "total_sources": 2,
        "total_claims": 2,
        "referenced_source_count": 2,
        "unused_source_count": 1,
        "missing_source_reference_count": 1,
        "sources_missing_metadata_count": 1,
        "source_type_counts": {
            "drug_label": 1,
            "internal_curation": 1,
        },
        "reliability_tier_counts": {
            "curated": 2,
        },
        "unused_sources": [
            {
                "source_id": "source_unused",
                "title": "Unused source",
            }
        ],
        "missing_source_references": [
            {
                "claim_id": "claim_a_001",
                "source_id": "source_missing",
            }
        ],
        "sources_missing_metadata": [
            {
                "source_id": "source_unused",
                "missing_fields": [
                    "url",
                    "published_at",
                    "accessed_at",
                ],
            }
        ],
    }


def test_format_report_text_shows_summary_and_missing_references():
    text = _format_report_text(_report())

    assert "Evidence source quality report" in text
    assert "Total evidence claims: 2" in text
    assert "Total source records: 2" in text
    assert "Missing source references: 1" in text
    assert "claim_a_001 -> source_missing" in text
    assert "source_unused: Unused source" not in text


def test_format_report_text_can_show_unused_sources():
    text = _format_report_text(_report(), show_unused=True)

    assert "Unused sources:" in text
    assert "source_unused: Unused source" in text


def test_format_report_text_can_show_metadata_gaps():
    text = _format_report_text(_report(), show_metadata=True)

    assert "Sources missing recommended metadata:" in text
    assert "source_unused: url, published_at, accessed_at" in text