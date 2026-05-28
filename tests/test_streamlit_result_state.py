from app.streamlit_ui.result_state import analysis_state_from_payload


def test_analysis_state_from_payload_extracts_success_payload_fields():
    facts = object()
    pair_report = object()
    regimen_summary = {"severity": "caution"}
    public_summary = object()
    aggregate_summary = object()

    payload = {
        "facts": facts,
        "drug_ids": ["clarithromycin", "fluconazole"],
        "pair_reports": [pair_report],
        "templates": {"shared_qt": "Shared QT concern"},
        "selected_domains": ["pk", "pd"],
        "regimen_summary": regimen_summary,
        "public_result_summaries": [public_summary],
        "aggregate_concern_summaries": [aggregate_summary],
        "mechanism_pipeline_json": {"stages": []},
    }

    state = analysis_state_from_payload(payload)

    assert state.payload is payload
    assert state.facts is facts
    assert state.drug_ids == ["clarithromycin", "fluconazole"]
    assert state.pair_reports == [pair_report]
    assert state.templates == {"shared_qt": "Shared QT concern"}
    assert state.selected_domains == ["pk", "pd"]
    assert state.regimen_summary == regimen_summary
    assert state.public_result_summaries == [public_summary]
    assert state.aggregate_concern_summaries == [aggregate_summary]


def test_analysis_state_from_payload_defaults_optional_summary_fields():
    payload = {
        "facts": object(),
        "drug_ids": ["clarithromycin"],
        "pair_reports": [],
        "templates": {},
        "selected_domains": ["all"],
    }

    state = analysis_state_from_payload(payload)

    assert state.regimen_summary is None
    assert state.public_result_summaries == []
    assert state.aggregate_concern_summaries == []