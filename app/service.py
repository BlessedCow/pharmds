from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.cli import (
    DB_PATH,
    RULE_DIR,
    _collect_drug_inputs,
    _parse_domain_selection,
    _parse_drug_tokens,
    _build_reports_for_all_pairs,
    connect,
    filter_rules_for_selected_domains,
    load_facts,
    resolve_drug_ids,
)
from app.json_output import build_json_payload
from core.exceptions import UnknownDrugError
from reasoning.combine import build_regimen_summary
from rules.engine import evaluate_all, load_rules


@dataclass(frozen=True)
class AnalyzeResult:
    """Small typed wrapper so Streamlit callers have predictable keys.

    - ok: False when there is a user-correctable issue (too few drugs, unknown drugs, etc.)
    - payload: success payload (facts/reports/templates/etc.) or error payload
    """

    ok: bool
    payload: dict[str, Any]


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

    patient_flags = {
        "qt_risk": bool(qt_risk),
        "bleeding_risk": bool(bleeding_risk),
    }

    conn = connect(DB_PATH)

    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
    except UnknownDrugError as e:
        return AnalyzeResult(
            ok=False,
            payload={
                "error": "unknown_drug",
                "unknown": list(e.unknown),
                "suggestions": dict(e.suggestions or {}),
                "input_drug_names": drug_names,
            },
        )

    facts = load_facts(conn, drug_ids, patient_flags)

    selected = _parse_domain_selection(domain)

    rules_all = load_rules(RULE_DIR)
    rules = filter_rules_for_selected_domains(rules_all, selected)

    hits = evaluate_all(rules, facts, drug_ids)

    from rules.composite_rules import apply_composites

    hits = apply_composites(facts, hits)

    templates = {r.id: r.explanation_template for r in rules}
    pair_reports = _build_reports_for_all_pairs(facts, hits, templates, drug_ids)

    regimen_summary = None
    if len(drug_ids) >= 3:
        regimen_summary = build_regimen_summary(facts, pair_reports)

    if as_json_payload:
        payload = build_json_payload(
            facts=facts,
            reports=pair_reports,
            templates=templates,
            selected_domains=selected,
            input_drug_names=drug_names,
            patient_flags=patient_flags,
            regimen_summary=regimen_summary,
        )
        if input_drug_text is not None:
            payload["input_drug_text"] = input_drug_text
        return AnalyzeResult(ok=True, payload=payload)

    # Default: return python objects for rich Streamlit rendering
    return AnalyzeResult(
        ok=True,
        payload={
            "facts": facts,
            "drug_ids": drug_ids,
            "pair_reports": pair_reports,
            "templates": templates,
            "selected_domains": selected,
            "patient_flags": patient_flags,
            "input_drug_names": drug_names,
            "regimen_summary": regimen_summary,
        },
    )