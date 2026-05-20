from tools.evidence_gap_report import _format_report_text


def test_format_report_text_hides_complete_items_by_default():
    report = {
        "total_pd_effects": 3,
        "gap_count": 1,
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
        "gaps_by_pd_effect": {
            "sedation": [
                {
                    "drug_id": "drug_b",
                    "effect_id": "sedation",
                    "classification": "missing",
                    "coverage_status": "missing",
                    "confidence_level": None,
                    "claim_count": 0,
                    "source_types": ["no_source"],
                }
            ],
        },
        "gaps_by_drug": {
            "drug_b": [
                {
                    "drug_id": "drug_b",
                    "effect_id": "sedation",
                    "classification": "missing",
                    "coverage_status": "missing",
                    "confidence_level": None,
                    "claim_count": 0,
                    "source_types": ["no_source"],
                }
            ],
        },
        "gaps_by_source_type": {
            "no_source": [
                {
                    "drug_id": "drug_b",
                    "effect_id": "sedation",
                    "classification": "missing",
                    "coverage_status": "missing",
                    "confidence_level": None,
                    "claim_count": 0,
                    "source_types": ["no_source"],
                }
            ],
        },
        "items": [
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "classification": "moderate_confidence",
                "coverage_status": "complete",
                "confidence_level": "moderate",
                "claim_count": 1,
                "source_types": ["drug_label"],
            },
            {
                "drug_id": "drug_b",
                "effect_id": "sedation",
                "classification": "missing",
                "coverage_status": "missing",
                "confidence_level": None,
                "claim_count": 0,
                "source_types": ["no_source"],
            },
        ],
    }

    text = _format_report_text(report)

    assert "PD effect evidence gap report" in text
    assert "Missing/partial evidence rows: 1" in text
    assert "Grouped by PD effect:" in text
    assert "Grouped by drug:" in text
    assert "Grouped by source type:" in text
    assert "drug_b -> sedation: missing" in text
    assert "drug_a -> nausea" not in text


def test_format_report_text_can_show_complete_items():
    report = {
        "total_pd_effects": 1,
        "gap_count": 0,
        "coverage_counts": {
            "complete": 1,
        },
        "confidence_counts": {
            "high_confidence": 1,
        },
        "classification_counts": {
            "high_confidence": 1,
        },
        "gaps_by_pd_effect": {},
        "gaps_by_drug": {},
        "gaps_by_source_type": {},
        "items": [
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "classification": "high_confidence",
                "coverage_status": "complete",
                "confidence_level": "high",
                "claim_count": 1,
                "source_types": ["drug_label"],
            },
        ],
    }

    text = _format_report_text(report, show_complete=True)

    assert "Grouped by PD effect:\n  none" in text
    assert "Complete/moderate/high rows:" in text
    assert "drug_a -> nausea: high_confidence" in text
    assert "source_types=drug_label" in text