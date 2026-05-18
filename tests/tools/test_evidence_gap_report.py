from tools.evidence_gap_report import _format_report_text


def test_format_report_text_hides_complete_items_by_default():
    report = {
        "total_pd_effects": 3,
        "coverage_counts": {
            "complete": 2,
            "missing": 1,
        },
        "confidence_counts": {
            "moderate_confidence": 1,
            "no_confidence": 1,
        },
        "classification_counts": {
            "moderate_confidence": 1,
            "missing": 1,
        },
        "items": [
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "classification": "moderate_confidence",
                "coverage_status": "complete",
                "confidence_level": "moderate",
                "claim_count": 1,
            },
            {
                "drug_id": "drug_b",
                "effect_id": "sedation",
                "classification": "missing",
                "coverage_status": "missing",
                "confidence_level": None,
                "claim_count": 0,
            },
        ],
    }

    text = _format_report_text(report)

    assert "PD effect evidence gap report" in text
    assert "drug_b -> sedation: missing" in text
    assert "drug_a -> nausea" not in text


def test_format_report_text_can_show_complete_items():
    report = {
        "total_pd_effects": 1,
        "coverage_counts": {
            "complete": 1,
        },
        "confidence_counts": {
            "high_confidence": 1,
        },
        "classification_counts": {
            "high_confidence": 1,
        },
        "items": [
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "classification": "high_confidence",
                "coverage_status": "complete",
                "confidence_level": "high",
                "claim_count": 1,
            },
        ],
    }

    text = _format_report_text(report, show_complete=True)

    assert "drug_a -> nausea: high_confidence" in text