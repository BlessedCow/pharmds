"""Helpers for reading Streamlit analysis result payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StreamlitAnalysisState:
    """Display-ready values extracted from an AnalyzeResult payload."""

    payload: dict[str, Any]
    facts: Any
    drug_ids: list[str]
    pair_reports: list[Any]
    templates: dict[str, str]
    selected_domains: list[str]
    regimen_summary: dict[str, Any] | None
    public_result_summaries: list[Any]
    aggregate_concern_summaries: list[Any]


def analysis_state_from_payload(
    payload: dict[str, Any],
) -> StreamlitAnalysisState:
    """Extract stable UI fields from a successful analysis payload."""
    return StreamlitAnalysisState(
        payload=payload,
        facts=payload["facts"],
        drug_ids=list(payload["drug_ids"]),
        pair_reports=list(payload["pair_reports"]),
        templates=dict(payload["templates"]),
        selected_domains=list(payload["selected_domains"]),
        regimen_summary=payload.get("regimen_summary"),
        public_result_summaries=list(
            payload.get("public_result_summaries", [])
        ),
        aggregate_concern_summaries=list(
            payload.get("aggregate_concern_summaries", [])
        ),
    )