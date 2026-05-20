from app.service import analyze_text


def test_analyze_text_streamlit_payload_includes_mechanism_summaries():
    result = analyze_text(
        "clarithromycin fluconazole",
        as_json_payload=False,
    )

    assert result.ok

    payload = result.payload

    assert "mechanism_pipeline" in payload
    assert "mechanism_pipeline_json" in payload
    assert "public_result_summaries" in payload
    assert "aggregate_concern_summaries" in payload

    assert payload["mechanism_pipeline"].aggregate_concern_summaries
    assert payload["mechanism_pipeline_json"]["aggregate_concern_summaries"]
    assert payload["public_result_summaries"]
    assert payload["aggregate_concern_summaries"]


def test_analyze_text_json_payload_includes_public_summaries_and_debug_pipeline():
    result = analyze_text(
        "clarithromycin fluconazole",
        as_json_payload=True,
    )

    assert result.ok

    payload = result.payload

    assert "mechanism_pipeline" in payload
    assert "public_result_summaries" in payload

    assert payload["mechanism_pipeline"]["aggregate_concern_summaries"]
    assert payload["public_result_summaries"]

    summary = payload["public_result_summaries"][0]

    assert set(summary) == {
        "source",
        "title",
        "drugs",
        "concern_type",
        "severity_label",
        "evidence_label",
        "explanation",
    }