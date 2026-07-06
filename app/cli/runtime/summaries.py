from __future__ import annotations

from core.mechanisms import run_mechanism_pipeline
from core.mechanisms.result_summary import build_public_result_summaries
from reasoning.combine import build_regimen_summary


def build_cli_summaries(
    args,
    *,
    facts,
    drug_ids,
    pair_reports,
):
    regimen_summary = None
    if len(drug_ids) >= 3:
        regimen_summary = build_regimen_summary(facts, pair_reports)

    mechanism_pipeline = run_mechanism_pipeline(
        drug_ids,
        facts,
        evidence_mode=args.evidence_mode,
    )
    public_result_summaries = build_public_result_summaries(mechanism_pipeline)

    return regimen_summary, mechanism_pipeline, public_result_summaries