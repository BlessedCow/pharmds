from __future__ import annotations

from app.runtime.domains import filter_facts_for_selected_pd_effects
from core.mechanisms import run_mechanism_pipeline
from core.mechanisms.result_summary import build_public_result_summaries
from reasoning.combine import build_regimen_summary


def build_runtime_summaries(
    args,
    *,
    facts,
    drug_ids,
    pair_reports,
):
    mechanism_facts = filter_facts_for_selected_pd_effects(
        facts,
        getattr(args, "pd_effects", None),
    )

    regimen_summary = None
    if len(drug_ids) >= 3:
        regimen_summary = build_regimen_summary(
            mechanism_facts,
            pair_reports,
        )

    mechanism_pipeline = run_mechanism_pipeline(
        drug_ids,
        mechanism_facts,
        evidence_mode=args.evidence_mode,
    )
    public_result_summaries = build_public_result_summaries(
        mechanism_pipeline,
        pair_reports,
    )

    return regimen_summary, mechanism_pipeline, public_result_summaries
