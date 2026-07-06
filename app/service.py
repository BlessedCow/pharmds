from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from app.cli import DB_PATH, RULE_DIR
from app.cli.facts import connect, load_facts
from app.cli.inputs import (
    _collect_drug_inputs,
    _format_unknown_drug_message,
    _parse_drug_tokens,
    resolve_drug_ids,
)
from app.cli.runtime import (
    build_cli_pair_reports,
    build_cli_summaries,
    build_patient_flags,
)
from app.json_output import build_json_payload
from core.exceptions import UnknownDrugError
from core.mechanisms.pipeline_json import mechanism_pipeline_to_json_dict
from core.mechanisms.result_summary import (
    ResultSummary,
    result_summaries_to_json_dicts,
)


@dataclass(frozen=True)
class AnalyzeResult:
    """
    Small typed wrapper so Streamlit callers have predictable keys.

    - ok: False when there is a user-correctable issue
    (too few drugs, unknown drugs, etc.)
    - payload: success payload (facts/reports/templates/etc.)
    or error payload
    """

    ok: bool
    payload: dict[str, Any]


def _build_json_analyze_payload(
    *,
    facts: Any,
    pair_reports: list[Any],
    templates: dict[str, str],
    selected_domains: list[str],
    input_drug_names: list[str],
    patient_flags: dict[str, bool],
    regimen_summary: dict[str, Any] | None,
    mechanism_pipeline_json: dict[str, Any],
    public_result_summaries: list[ResultSummary],
    input_drug_text: str | None,
) -> dict[str, Any]:
    """Build the JSON/API-oriented success payload."""
    payload = build_json_payload(
        facts=facts,
        reports=pair_reports,
        templates=templates,
        selected_domains=selected_domains,
        input_drug_names=input_drug_names,
        patient_flags=patient_flags,
        regimen_summary=regimen_summary,
    )

    payload["mechanism_pipeline"] = mechanism_pipeline_json
    payload["public_result_summaries"] = result_summaries_to_json_dicts(
        public_result_summaries,
    )

    if input_drug_text is not None:
        payload["input_drug_text"] = input_drug_text

    return payload


def _build_streamlit_analyze_payload(
    *,
    facts: Any,
    drug_ids: list[str],
    pair_reports: list[Any],
    templates: dict[str, str],
    selected_domains: list[str],
    patient_flags: dict[str, bool],
    input_drug_names: list[str],
    regimen_summary: dict[str, Any] | None,
    mechanism_pipeline: Any,
    mechanism_pipeline_json: dict[str, Any],
    public_result_summaries: list[ResultSummary],
) -> dict[str, Any]:
    """Build the Streamlit-oriented success payload."""
    return {
        "facts": facts,
        "drug_ids": drug_ids,
        "pair_reports": pair_reports,
        "templates": templates,
        "selected_domains": selected_domains,
        "patient_flags": patient_flags,
        "input_drug_names": input_drug_names,
        "regimen_summary": regimen_summary,
        "mechanism_pipeline": mechanism_pipeline,
        "mechanism_pipeline_json": mechanism_pipeline_json,
        "public_result_summaries": public_result_summaries,
        "aggregate_concern_summaries": tuple(
            mechanism_pipeline.aggregate_concern_summaries
        ),
    }


def analyze_text(
    drug_text: str,
    *,
    domain: str = "all",
    qt_risk: bool = False,
    bleeding_risk: bool = False,
    as_json_payload: bool = False,
) -> AnalyzeResult:
    """
    Analyze drug interactions from free-form text input.

    """
    tokens = _parse_drug_tokens(drug_text)
    drug_names = _collect_drug_inputs(tokens, [])

    return analyze_names(
        drug_names,
        domain=domain,
        qt_risk=qt_risk,
        bleeding_risk=bleeding_risk,
        as_json_payload=as_json_payload,
        input_drug_text=drug_text,
    )


def analyze_names(
    drug_names: list[str],
    *,
    domain: str = "all",
    qt_risk: bool = False,
    bleeding_risk: bool = False,
    as_json_payload: bool = False,
    input_drug_text: str | None = None,
) -> AnalyzeResult:
    """
    Analyze drug interactions from a list of drug strings.

    Useful for programmatic calls/tests, or if you later add multi-select widgets.
    """
    if len(drug_names) < 2:
        return AnalyzeResult(
            ok=False,
            payload={
                "error": "Provide at least two drugs (generic or alias).",
                "input_drug_names": drug_names,
            },
        )

    patient_flags = build_patient_flags(
        SimpleNamespace(
            qt_risk=bool(qt_risk),
            bleeding_risk=bool(bleeding_risk),
        )
    )

    conn = connect(DB_PATH)

    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
    except UnknownDrugError as e:
        messages = [
            _format_unknown_drug_message(tok, e.suggestions.get(tok, ()))
            for tok in e.unknown
        ]
        return AnalyzeResult(
            ok=False,
            payload={
                "error": "unknown_drug",
                "unknown": list(e.unknown),
                "suggestions": dict(e.suggestions or {}),
                "message": " ".join(messages),
                "tip": (
                    "Common separators such as spaces, hyphens, slashes, and "
                    "underscores are treated the same."
                ),
                "input_drug_names": drug_names,
            },
        )
    facts = load_facts(conn, drug_ids, patient_flags)

    selected, templates, pair_reports = build_cli_pair_reports(
        SimpleNamespace(domain=domain),
        facts=facts,
        drug_ids=drug_ids,
        rule_dir=RULE_DIR,
    )

    summary_args = SimpleNamespace(evidence_mode="off")
    regimen_summary, mechanism_pipeline, public_result_summaries = build_cli_summaries(
        summary_args,
        facts=facts,
        drug_ids=drug_ids,
        pair_reports=pair_reports,
    )
    mechanism_pipeline_json = mechanism_pipeline_to_json_dict(
        mechanism_pipeline,
    )

    if as_json_payload:
        return AnalyzeResult(
            ok=True,
            payload=_build_json_analyze_payload(
                facts=facts,
                pair_reports=pair_reports,
                templates=templates,
                selected_domains=selected,
                input_drug_names=drug_names,
                patient_flags=patient_flags,
                regimen_summary=regimen_summary,
                mechanism_pipeline_json=mechanism_pipeline_json,
                public_result_summaries=public_result_summaries,
                input_drug_text=input_drug_text,
            ),
        )

    return AnalyzeResult(
        ok=True,
        payload=_build_streamlit_analyze_payload(
            facts=facts,
            drug_ids=drug_ids,
            pair_reports=pair_reports,
            templates=templates,
            selected_domains=selected,
            patient_flags=patient_flags,
            input_drug_names=drug_names,
            regimen_summary=regimen_summary,
            mechanism_pipeline=mechanism_pipeline,
            mechanism_pipeline_json=mechanism_pipeline_json,
            public_result_summaries=public_result_summaries,
        ),
    )