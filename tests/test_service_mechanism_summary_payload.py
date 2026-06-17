from types import SimpleNamespace

from app.service import (
    _build_json_analyze_payload,
    _build_streamlit_analyze_payload,
    analyze_names,
    analyze_text,
)
from core.mechanisms.result_summary import ResultSummary


def test_analyze_text_streamlit_payload_includes_stable_top_level_keys():
    result = analyze_text(
        "clarithromycin fluconazole",
        as_json_payload=False,
    )

    assert result.ok

    payload = result.payload

    assert set(payload) == {
        "facts",
        "drug_ids",
        "pair_reports",
        "templates",
        "selected_domains",
        "patient_flags",
        "input_drug_names",
        "regimen_summary",
        "mechanism_pipeline",
        "mechanism_pipeline_json",
        "public_result_summaries",
        "aggregate_concern_summaries",
    }


def test_analyze_text_streamlit_payload_includes_mechanism_summaries():
    result = analyze_text(
        "clarithromycin fluconazole",
        as_json_payload=False,
    )

    assert result.ok

    payload = result.payload

    assert payload["mechanism_pipeline"].aggregate_concern_summaries
    assert payload["mechanism_pipeline_json"]["aggregate_concern_summaries"]
    assert payload["public_result_summaries"]
    assert payload["aggregate_concern_summaries"]

def test_analyze_text_json_payload_includes_stable_top_level_keys():
    result = analyze_text(
        "clarithromycin fluconazole",
        as_json_payload=True,
    )

    assert result.ok

    payload = result.payload

    assert set(payload) == {
        "schema_version",
        "input",
        "input_drug_text",
        "pairs",
        "mechanism_pipeline",
        "public_result_summaries",
    }

def test_analyze_text_json_payload_includes_public_summaries_and_debug_pipeline():
    result = analyze_text(
        "clarithromycin fluconazole",
        as_json_payload=True,
    )

    assert result.ok

    payload = result.payload

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

def test_analyze_names_unknown_drug_payload_includes_actionable_message():
    result = analyze_names(["quetiaipne", "fluconazole"])

    assert not result.ok

    payload = result.payload
    assert payload["error"] == "unknown_drug"
    assert payload["unknown"] == ["quetiaipne"]
    assert "quetiapine" in payload["suggestions"]["quetiaipne"]
    assert "Drug 'quetiaipne' was not found. Did you mean: quetiapine" in (
        payload["message"]
    )
    assert "Common separators" in payload["tip"]
    assert payload["input_drug_names"] == ["quetiaipne", "fluconazole"]


def test_analyze_text_resolves_aliases_with_common_separator_variants():
    result = analyze_text("wellbutrin-xl\namphetamine/dextroamphetamine")

    assert result.ok
    assert result.payload["drug_ids"] == [
        "bupropion",
        "amphetamine_dextroamphetamine",
    ]
    
def test_analyze_names_deduplicates_canonical_drug_ids_after_alias_resolution():
    result = analyze_names(["wellbutrin-xl", "bupropion", "diflucan"])

    assert result.ok
    assert result.payload["drug_ids"] == [
        "bupropion",
        "fluconazole",
    ]
    
def test_build_json_analyze_payload_converts_public_summaries_to_dicts():
    public_summary = ResultSummary(
        source="aggregate_summary",
        title="Shared QT prolongation concern",
        drugs=("clarithromycin", "fluconazole"),
        concern_type="cardiac_rhythm",
        severity_label="moderate",
        evidence_label="complete",
        explanation="Both drugs are associated with QT prolongation.",
    )

    payload = _build_json_analyze_payload(
        facts=object(),
        pair_reports=[],
        templates={},
        selected_domains=["all"],
        input_drug_names=["clarithromycin", "fluconazole"],
        patient_flags={"qt_risk": False, "bleeding_risk": False},
        regimen_summary=None,
        mechanism_pipeline_json={"aggregate_concern_summaries": []},
        public_result_summaries=[public_summary],
        input_drug_text="clarithromycin fluconazole",
    )

    assert payload["schema_version"] == "1.0"
    assert payload["input_drug_text"] == "clarithromycin fluconazole"
    assert payload["mechanism_pipeline"] == {
        "aggregate_concern_summaries": []
    }
    assert payload["public_result_summaries"] == [
        {
            "source": "aggregate_summary",
            "title": "Shared QT prolongation concern",
            "drugs": ["clarithromycin", "fluconazole"],
            "concern_type": "cardiac_rhythm",
            "severity_label": "moderate",
            "evidence_label": "complete",
            "explanation": (
                "Both drugs are associated with QT prolongation."
            ),
        }
    ]


def test_build_streamlit_analyze_payload_preserves_ui_objects():
    facts = object()
    pair_report = object()
    public_summary = object()
    aggregate_summary = object()
    mechanism_pipeline = SimpleNamespace(
        aggregate_concern_summaries=(aggregate_summary,),
    )
    mechanism_pipeline_json = {"aggregate_concern_summaries": [{}]}

    payload = _build_streamlit_analyze_payload(
        facts=facts,
        drug_ids=["clarithromycin", "fluconazole"],
        pair_reports=[pair_report],
        templates={"rule": "template"},
        selected_domains=["all"],
        patient_flags={"qt_risk": False, "bleeding_risk": False},
        input_drug_names=["clarithromycin", "fluconazole"],
        regimen_summary=None,
        mechanism_pipeline=mechanism_pipeline,
        mechanism_pipeline_json=mechanism_pipeline_json,
        public_result_summaries=[public_summary],
    )

    assert payload == {
        "facts": facts,
        "drug_ids": ["clarithromycin", "fluconazole"],
        "pair_reports": [pair_report],
        "templates": {"rule": "template"},
        "selected_domains": ["all"],
        "patient_flags": {"qt_risk": False, "bleeding_risk": False},
        "input_drug_names": ["clarithromycin", "fluconazole"],
        "regimen_summary": None,
        "mechanism_pipeline": mechanism_pipeline,
        "mechanism_pipeline_json": mechanism_pipeline_json,
        "public_result_summaries": [public_summary],
        "aggregate_concern_summaries": (aggregate_summary,),
    }