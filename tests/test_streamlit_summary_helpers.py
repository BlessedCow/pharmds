from app.streamlit_ui.summary_helpers import (
    aggregate_summary_debug_fields,
    aggregate_summary_debug_lines,
    result_summaries_to_streamlit_cards,
    result_summary_to_streamlit_card,
)
from core.mechanisms.result_summary import ResultSummary


def test_result_summary_to_streamlit_card_formats_public_summary():
    summary = ResultSummary(
        source="aggregate_summary",
        title="Shared nausea concern",
        drugs=("clarithromycin", "fluconazole"),
        concern_type="tolerability_concern",
        severity_label="caution",
        evidence_label="complete",
        explanation="These drugs share a nausea-related concern.",
    )

    card = result_summary_to_streamlit_card(summary)

    assert card == {
        "source": "aggregate_summary",
        "title": "Shared nausea concern",
        "drugs": "clarithromycin and fluconazole",
        "concern_type": "tolerability_concern",
        "concern_type_label": "Tolerability concern",
        "severity_label": "caution",
        "severity_display": "Caution",
        "evidence_label": "complete",
        "evidence_display": "Complete",
        "explanation": "These drugs share a nausea-related concern.",
    }

def test_result_summaries_to_streamlit_cards_dedupes_shared_display_variants():
    summaries = [
        ResultSummary(
            source="aggregate_summary",
            title="Shared QT prolongation concern",
            drugs=("clarithromycin", "fluconazole"),
            concern_type="safety_concern",
            severity_label="high_caution",
            evidence_label="complete",
            explanation="Shared QT concern.",
        ),
        ResultSummary(
            source="aggregate_summary",
            title="QT prolongation concern",
            drugs=("clarithromycin", "fluconazole"),
            concern_type="safety_concern",
            severity_label="high_caution",
            evidence_label="complete",
            explanation="Grouped QT concern.",
        ),
    ]

    cards = result_summaries_to_streamlit_cards(summaries)

    assert len(cards) == 1
    assert cards[0]["title"] == "Shared QT prolongation concern"
    assert cards[0]["summary_index"] == 0

def test_result_summary_to_streamlit_card_handles_missing_text():
    summary = ResultSummary(
        source="aggregate_summary",
        title="",
        drugs=(),
        concern_type="",
        severity_label="",
        evidence_label="",
        explanation="",
    )

    card = result_summary_to_streamlit_card(summary)

    assert card["title"] == "Summary"
    assert card["drugs"] == "No drugs listed"
    assert card["concern_type"] == "not_available"
    assert card["concern_type_label"] == "not_available"
    assert card["severity_label"] == "not_available"
    assert card["severity_display"] == "not_available"
    assert card["evidence_label"] == "not_available"
    assert card["evidence_display"] == "not_available"
    assert card["explanation"] == "No explanation available."


def test_aggregate_summary_debug_fields_extracts_compact_details():
    aggregate_summary = {
        "aggregate": {
            "aggregate_type": "shared_pd_effect",
            "policy_concern": "tolerability_concern",
            "anchor": "nausea",
            "effect_id": "nausea",
            "targets": [],
        },
        "severity_annotation": {
            "strongest_preliminary_severity": "caution",
        },
        "evidence_summary": {
            "overall_evidence_status": "complete",
            "evidence_claim_count": 2,
            "evidence_gap_count": 0,
            "evidence_trace_count": 2,
        },
        "patient_risk_modifiers": ["qt_risk"],
        "risk_context": "QT risk factors present.",
        "evidence_conflict_message": None,
    }

    fields = aggregate_summary_debug_fields(aggregate_summary)

    assert fields["aggregate_type"] == "shared_pd_effect"
    assert fields["policy_concern"] == "tolerability_concern"
    assert fields["anchor"] == "nausea"
    assert fields["effect_id"] == "nausea"
    assert fields["effect_label"] == "nausea"
    assert fields["severity"] == "caution"
    assert fields["evidence_status"] == "complete"
    assert fields["evidence_claim_count"] == 2
    assert fields["evidence_gap_count"] == 0
    assert fields["patient_risk_modifiers"] == ["qt_risk"]


def test_aggregate_summary_debug_lines_include_optional_context():
    aggregate_summary = {
        "aggregate": {
            "aggregate_type": "object_exposure_increase",
            "policy_concern": "mechanistic_concern",
            "anchor": "vortioxetine",
            "effect_id": None,
            "targets": ["CYP2D6"],
        },
        "severity_annotation": {
            "strongest_preliminary_severity": "informational",
        },
        "evidence_summary": {
            "overall_evidence_status": "not_applicable",
            "evidence_claim_count": 0,
            "evidence_gap_count": 0,
            "evidence_trace_count": 0,
            "evidence_conflict_reasons": [
                "claim_disagreement",
                "source_mismatch",
            ],
        },
        "patient_risk_modifiers": [],
        "risk_context": None,
        "evidence_conflict_message": "Conflicting evidence was found.",
    }

    lines = aggregate_summary_debug_lines(aggregate_summary)

    assert "Aggregate type: object_exposure_increase" in lines
    assert "Targets: CYP2D6" in lines
    assert "Evidence conflict: Conflicting evidence was found." in lines
    assert (
        "Evidence conflict reasons: claim disagreement, mixed source types"
        in lines
    )
    
def test_aggregate_summary_debug_fields_accepts_dataclass_summary():
    from core.mechanisms.aggregate_evidence import AggregateEvidenceSummary
    from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
    from core.mechanisms.aggregate_summary import AggregateConcernSummary
    from core.mechanisms.aggregation import AggregateConcern

    aggregate = AggregateConcern(
        aggregate_type="shared_pd_effect_cluster",
        anchor="QT_prolongation",
        policy_concern="safety_concern",
        drugs=("clarithromycin", "fluconazole"),
        effect_id="QT_prolongation",
    )
    aggregate_summary = AggregateConcernSummary(
        aggregate=aggregate,
        severity_annotation=AggregateSeverityAnnotation(
            aggregate=aggregate,
            strongest_preliminary_severity="high_caution",
        ),
        evidence_summary=AggregateEvidenceSummary(
            aggregate=aggregate,
            overall_evidence_status="complete",
            evidence_claim_count=2,
            evidence_trace_count=2,
        ),
        patient_risk_modifiers=("qt_risk",),
        risk_context="QT-related concern may be more important.",
    )

    fields = aggregate_summary_debug_fields(aggregate_summary)

    assert fields["aggregate_type"] == "shared_pd_effect_cluster"
    assert fields["policy_concern"] == "safety_concern"
    assert fields["anchor"] == "QT_prolongation"
    assert fields["effect_id"] == "QT_prolongation"
    assert fields["effect_label"] == "QT_prolongation (QT prolongation)"
    assert fields["severity"] == "high_caution"
    assert fields["evidence_status"] == "complete"
    assert fields["evidence_claim_count"] == 2
    assert fields["evidence_trace_count"] == 2
    assert fields["patient_risk_modifiers"] == ["qt_risk"]
    
def test_aggregate_summary_debug_lines_show_readable_effect_label():
    aggregate_summary = {
        "aggregate": {
            "aggregate_type": "shared_pd_effect_cluster",
            "policy_concern": "safety_concern",
            "anchor": "QT_prolongation",
            "effect_id": "QT_prolongation",
            "targets": [],
        },
        "severity_annotation": {
            "strongest_preliminary_severity": "high_caution",
        },
        "evidence_summary": {
            "overall_evidence_status": "complete",
            "evidence_claim_count": 2,
            "evidence_gap_count": 0,
            "evidence_trace_count": 2,
        },
        "patient_risk_modifiers": [],
        "risk_context": None,
        "evidence_conflict_message": None,
    }

    lines = aggregate_summary_debug_lines(aggregate_summary)

    assert "Effect: QT_prolongation (QT prolongation)" in lines
    
def test_aggregate_summary_debug_lines_show_readable_evidence_sources():
    aggregate_summary = {
        "aggregate": {
            "aggregate_type": "shared_pd_effect_cluster",
            "policy_concern": "safety_concern",
            "anchor": "QT_prolongation",
            "effect_id": "QT_prolongation",
            "targets": [],
        },
        "severity_annotation": {
            "strongest_preliminary_severity": "high_caution",
        },
        "evidence_summary": {
            "overall_evidence_status": "complete",
            "evidence_claim_count": 2,
            "evidence_gap_count": 0,
            "evidence_trace_count": 2,
            "evidence_source_ids": [
                "source_dailymed_clarithromycin_label",
            ],
        },
        "patient_risk_modifiers": [],
        "risk_context": None,
        "evidence_conflict_message": None,
    }

    lines = aggregate_summary_debug_lines(aggregate_summary)

    assert (
        "Evidence sources: 1 source: Clarithromycin Prescribing "
        "Information (drug_label)"
    ) in lines


def test_aggregate_summary_debug_lines_show_none_for_missing_sources():
    aggregate_summary = {
        "aggregate": {
            "aggregate_type": "shared_pd_effect_cluster",
            "policy_concern": "tolerability_concern",
            "anchor": "nausea",
            "effect_id": "nausea",
            "targets": [],
        },
        "severity_annotation": None,
        "evidence_summary": {
            "overall_evidence_status": "missing",
            "evidence_claim_count": 0,
            "evidence_gap_count": 2,
            "evidence_trace_count": 1,
            "evidence_source_ids": [],
        },
        "patient_risk_modifiers": [],
        "risk_context": None,
        "evidence_conflict_message": None,
    }

    lines = aggregate_summary_debug_lines(aggregate_summary)

    assert "Evidence sources: none" in lines