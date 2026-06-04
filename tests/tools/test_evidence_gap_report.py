from core.evidence.completeness import BACKFILL_PRIORITY_MISSING
from tools import evidence_gap_report


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

    text = evidence_gap_report._format_report_text(report)

    assert "PD effect evidence gap report" in text
    assert "Missing/partial evidence rows: 1" in text
    assert "Grouped by PD effect:" in text
    assert "Grouped by drug:" in text
    assert "Grouped by source type:" in text
    assert "drug_b -> sedation: missing" in text
    assert "drug_a -> nausea" not in text
    assert "Backfill planning report:" in text
    assert "No backfill tasks found." in text

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

    text = evidence_gap_report._format_report_text(
        report,
        show_complete=True,
    )

    assert "complete" in text


def test_format_report_text_includes_backfill_plan():
    report = {
        "total_pd_effects": 1,
        "gap_count": 1,
        "coverage_counts": {"missing": 1},
        "confidence_counts": {"none": 1},
        "classification_counts": {"missing": 1},
        "source_type_counts": {"no_source": 1},
        "gaps_by_pd_effect": {
            "nausea": [
                {
                    "drug_id": "drug_a",
                    "effect_id": "nausea",
                    "coverage_status": "missing",
                    "confidence_status": "none",
                    "classification": "missing",
                    "claim_count": 0,
                    "source_types": ["no_source"],
                }
            ]
        },
        "gaps_by_drug": {
            "drug_a": [
                {
                    "drug_id": "drug_a",
                    "effect_id": "nausea",
                    "coverage_status": "missing",
                    "confidence_status": "none",
                    "classification": "missing",
                    "claim_count": 0,
                    "source_types": ["no_source"],
                }
            ]
        },
        "gaps_by_source_type": {
            "no_source": [
                {
                    "drug_id": "drug_a",
                    "effect_id": "nausea",
                    "coverage_status": "missing",
                    "confidence_status": "none",
                    "classification": "missing",
                    "claim_count": 0,
                    "source_types": ["no_source"],
                }
            ]
        },
        "items": [
            {
                "drug_id": "drug_a",
                "effect_id": "nausea",
                "coverage_status": "missing",
                "confidence_status": "none",
                "classification": "missing",
                "claim_count": 0,
                "source_types": ["no_source"],
            }
        ],
        "backfill_plan": {
            "total_tasks": 1,
            "priority_counts": {BACKFILL_PRIORITY_MISSING: 1},
            "tasks": [
                {
                    "priority": BACKFILL_PRIORITY_MISSING,
                    "drug_id": "drug_a",
                    "effect_id": "nausea",
                    "coverage_status": "missing",
                    "confidence_level": None,
                    "confidence_status": "none",
                    "classification": "missing",
                    "claim_count": 0,
                    "source_types": ["no_source"],
                    "missing_source_types": ["drug_label"],
                    "suggested_next_action": (
                        "Add curated evidence claim(s), starting with "
                        "drug_label."
                    ),
                }
            ],
            "by_priority": {
                BACKFILL_PRIORITY_MISSING: [
                    {
                        "priority": BACKFILL_PRIORITY_MISSING,
                        "drug_id": "drug_a",
                        "effect_id": "nausea",
                        "coverage_status": "missing",
                        "confidence_level": None,
                        "confidence_status": "none",
                        "classification": "missing",
                        "claim_count": 0,
                        "source_types": ["no_source"],
                        "missing_source_types": ["drug_label"],
                        "suggested_next_action": (
                            "Add curated evidence claim(s), starting with "
                            "drug_label."
                        ),
                    }
                ]
            },
            "by_pd_effect": {
                "nausea": [
                    {
                        "priority": BACKFILL_PRIORITY_MISSING,
                        "drug_id": "drug_a",
                        "effect_id": "nausea",
                        "coverage_status": "missing",
                        "confidence_level": None,
                        "confidence_status": "none",
                        "classification": "missing",
                        "claim_count": 0,
                        "source_types": ["no_source"],
                        "missing_source_types": ["drug_label"],
                        "suggested_next_action": (
                            "Add curated evidence claim(s), starting with "
                            "drug_label."
                        ),
                    }
                ]
            },
            "by_drug": {
                "drug_a": [
                    {
                        "priority": BACKFILL_PRIORITY_MISSING,
                        "drug_id": "drug_a",
                        "effect_id": "nausea",
                        "coverage_status": "missing",
                        "confidence_level": None,
                        "confidence_status": "none",
                        "classification": "missing",
                        "claim_count": 0,
                        "source_types": ["no_source"],
                        "missing_source_types": ["drug_label"],
                        "suggested_next_action": (
                            "Add curated evidence claim(s), starting with "
                            "drug_label."
                        ),
                    }
                ]
            },
            "by_source_type": {
                "drug_label": [
                    {
                        "priority": BACKFILL_PRIORITY_MISSING,
                        "drug_id": "drug_a",
                        "effect_id": "nausea",
                        "coverage_status": "missing",
                        "confidence_level": None,
                        "confidence_status": "none",
                        "classification": "missing",
                        "claim_count": 0,
                        "source_types": ["no_source"],
                        "missing_source_types": ["drug_label"],
                        "suggested_next_action": (
                            "Add curated evidence claim(s), starting with "
                            "drug_label."
                        ),
                    }
                ]
            },
        },
    }

    text = evidence_gap_report._format_report_text(
        report,
        show_complete=False,
    )

    assert "Backfill planning report:" in text
    assert "Total backfill tasks: 1" in text
    assert BACKFILL_PRIORITY_MISSING in text
    assert "drug_a -> nausea" in text
    assert "missing_sources=drug_label" in text
    
def _format_current_gap_report_failure(report: dict) -> str:
    tasks = report.get("backfill_plan", {}).get("tasks", [])

    if not tasks:
        return (
            "Expected current PD effect evidence gap report to have zero "
            "missing/partial rows, but gap_count was nonzero."
        )

    lines = [
        "Expected current PD effect evidence gap report to have zero "
        "missing/partial rows.",
        "",
        "Remaining gaps:",
    ]

    for task in tasks:
        lines.append(
            "- "
            f"{task['drug_id']} -> {task['effect_id']}: "
            f"{task['classification']} "
            f"(coverage={task['coverage_status']}, "
            f"confidence={task['confidence_status']}, "
            f"claims={task['claim_count']})"
        )

    return "\n".join(lines)


def test_current_pd_effect_evidence_gap_report_has_zero_gaps():
    with evidence_gap_report.connect(evidence_gap_report.DB_PATH) as conn:
        drug_ids = evidence_gap_report._all_drug_ids(conn)
        facts = evidence_gap_report.load_facts(conn, drug_ids, {})

    report = evidence_gap_report.build_pd_effect_evidence_gap_report(facts)

    assert report["gap_count"] == 0, _format_current_gap_report_failure(report)
    assert report["backfill_plan"]["total_tasks"] == 0