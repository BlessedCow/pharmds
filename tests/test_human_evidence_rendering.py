from core.enums import Domain, RuleClass, Severity
from core.evidence.human_rendering import (
    build_human_evidence_lines_for_rule_hit,
    format_human_evidence_trace,
)
from core.models import Drug, Facts, RuleHit


def test_format_human_evidence_trace_returns_compact_lines():
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
                        "evidence": [
                            {
                                "evidence_type": "internal_curated_entry",
                                "supports_claim": True,
                                "confidence": "moderate",
                            }
                        ],
                    }
                ],
            },
            {
                "drug_id": "fluconazole",
                "effect_id": "nausea",
                "evidence_status": "present",
                "claims": [
                    {
                        "evidence": [
                            {
                                "evidence_type": "internal_curated_entry",
                                "supports_claim": True,
                                "confidence": "moderate",
                            }
                        ],
                    }
                ],
            },
        ],
    }

    assert format_human_evidence_trace(trace) == [
        "Evidence status: complete",
        (
            "clarithromycin: supported by curated PD effect claim, "
            "moderate confidence"
        ),
        (
            "fluconazole: supported by curated PD effect claim, "
            "moderate confidence"
        ),
    ]


def test_format_human_evidence_trace_handles_missing_claims():
    trace = {
        "overall_evidence_status": "partial",
        "drugs": [
            {
                "drug_id": "alprazolam",
                "effect_id": "nausea",
                "evidence_status": "missing",
                "claims": [],
            }
        ],
    }

    assert format_human_evidence_trace(trace) == [
        "Evidence status: partial",
        "alprazolam: no approved evidence claim found",
    ]


def test_build_human_evidence_lines_for_rule_hit_uses_drug_names():
    facts = Facts(
        drugs={
            "clarithromycin": Drug(
                id="clarithromycin",
                generic_name="Clarithromycin",
                drug_class="macrolide antibiotic",
                therapeutic_index="moderate",
            ),
            "fluconazole": Drug(
                id="fluconazole",
                generic_name="Fluconazole",
                drug_class="azole antifungal",
                therapeutic_index="moderate",
            ),
        },
    )
    hit = RuleHit(
        rule_id="PD_NAUSEA_ADDITIVE",
        name="Additive nausea risk",
        domain=Domain.PD,
        severity=Severity.caution,
        rule_class=RuleClass.adjust_monitor,
        inputs={
            "A": "clarithromycin",
            "B": "fluconazole",
            "effect_id": "nausea",
        },
    )

    assert build_human_evidence_lines_for_rule_hit(facts, hit) == [
        "Evidence status: complete",
        (
            "Clarithromycin: supported by curated PD effect claim, "
            "moderate confidence"
        ),
        (
            "Fluconazole: supported by curated PD effect claim, "
            "moderate confidence"
        ),
    ]


def test_build_human_evidence_lines_for_rule_hit_ignores_non_pd_shape():
    facts = Facts()
    hit = RuleHit(
        rule_id="EXAMPLE",
        name="Example",
        domain=Domain.PK,
        severity=Severity.info,
        rule_class=RuleClass.info,
        inputs={},
    )

    assert build_human_evidence_lines_for_rule_hit(facts, hit) == []