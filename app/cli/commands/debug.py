from __future__ import annotations

import json
from pathlib import Path

from app.cli.domains import (
    _parse_domain_selection,
    filter_rules_for_selected_domains,
)
from app.cli.pairwise import _build_reports_for_all_pairs
from app.cli.render.debug import (
    render_pairwise_migration_debug,
    render_severity_annotations,
    render_severity_comparison,
)
from app.cli.render.plain import (
    render_aggregate_concern_summaries,
    render_aggregate_evidence_summary,
)
from core.mechanisms import mechanism_pipeline_to_json_dict, run_mechanism_pipeline
from core.mechanisms.aggregation_debug import format_aggregate_concerns
from core.mechanisms.arbitration_debug import format_arbitration_results
from core.mechanisms.candidate_debug import format_interaction_candidates
from core.mechanisms.debug import (
    DEBUG_MECHANISM_PIPELINE_LABEL,
    DEBUG_PAIRWISE_MIGRATION_LABEL,
    format_debug_section_title,
    format_mechanism_effects,
)
from core.mechanisms.policy_debug import format_policy_results
from core.mechanisms.scoring_debug import format_scored_concerns
from rules.engine import evaluate_all, load_rules


def should_handle_mechanism_debug_command(args) -> bool:
    return any(
        (
            args.show_mechanisms,
            args.show_candidates,
            args.show_arbitration,
            args.show_policy,
            args.show_scored,
            args.show_aggregates,
            args.show_mechanism_json,
            args.show_severity,
            args.show_severity_comparison,
            args.show_aggregate_evidence,
            args.show_aggregate_summaries,
            args.show_pairwise_migration_debug,
        )
    )


def _print_debug_lines(
    section_label: str,
    section_title: str,
    lines: list[str],
) -> None:
    print(
        "\n"
        + format_debug_section_title(
            section_label,
            section_title,
        )
        + "\n"
    )
    for line in lines:
        print(f"- {line}")


def _build_pair_reports_for_migration_debug(
    args,
    facts,
    drug_ids,
    rule_dir: Path,
):
    rules_all = load_rules(rule_dir)
    selected = _parse_domain_selection(args.domain)
    rules = filter_rules_for_selected_domains(rules_all, selected)
    hits = evaluate_all(rules, facts, drug_ids)

    from rules.composite_rules import apply_composites

    hits = apply_composites(
        facts,
        hits,
        include_pk_pd_composites="pd" in selected,
    )
    templates = {rule.id: rule.explanation_template for rule in rules}

    return _build_reports_for_all_pairs(
        facts,
        hits,
        templates,
        drug_ids,
    )


def handle_mechanism_debug_command(
    args,
    facts,
    drug_ids,
    *,
    rule_dir: Path,
) -> bool:
    if not should_handle_mechanism_debug_command(args):
        return False

    pipeline = run_mechanism_pipeline(
        drug_ids,
        facts,
        evidence_mode=args.evidence_mode,
    )

    if args.show_mechanism_json:
        payload = mechanism_pipeline_to_json_dict(pipeline)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return True

    if args.show_mechanisms:
        _print_debug_lines(
            DEBUG_MECHANISM_PIPELINE_LABEL,
            "Normalized MechanismEffect IR",
            format_mechanism_effects(list(pipeline.effects)),
        )
        return True

    if args.show_candidates:
        _print_debug_lines(
            DEBUG_MECHANISM_PIPELINE_LABEL,
            "Candidate Interaction Patterns",
            format_interaction_candidates(list(pipeline.candidates)),
        )
        return True

    if args.show_arbitration:
        _print_debug_lines(
            DEBUG_MECHANISM_PIPELINE_LABEL,
            "Arbitration Results",
            format_arbitration_results(list(pipeline.arbitration_results)),
        )
        return True

    if args.show_policy:
        _print_debug_lines(
            DEBUG_MECHANISM_PIPELINE_LABEL,
            "Policy Results",
            format_policy_results(list(pipeline.policy_results)),
        )
        return True

    if args.show_scored:
        _print_debug_lines(
            DEBUG_MECHANISM_PIPELINE_LABEL,
            "Scored Concerns",
            format_scored_concerns(list(pipeline.scored_concerns)),
        )
        return True

    if args.show_severity:
        print(
            "\n"
            + format_debug_section_title(
                DEBUG_MECHANISM_PIPELINE_LABEL,
                "Severity Annotations",
            )
            + "\n"
        )
        print(render_severity_annotations(pipeline.severity_annotations))
        return True

    if args.show_severity_comparison:
        print(
            "\n"
            + format_debug_section_title(
                DEBUG_PAIRWISE_MIGRATION_LABEL,
                "Severity Comparison",
            )
        )
        print(render_severity_comparison(pipeline))
        return True

    if args.show_aggregate_evidence:
        if args.format == "json":
            payload = mechanism_pipeline_to_json_dict(pipeline)
            print(
                json.dumps(
                    {
                        "aggregate_evidence_summaries": payload[
                            "aggregate_evidence_summaries"
                        ],
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return True

        print(
            "\n"
            + format_debug_section_title(
                DEBUG_MECHANISM_PIPELINE_LABEL,
                "Aggregate Evidence Summary",
            )
        )
        print(render_aggregate_evidence_summary(pipeline))
        return True

    if args.show_aggregate_summaries:
        if args.format == "json":
            payload = mechanism_pipeline_to_json_dict(pipeline)
            summaries = payload["aggregate_concern_summaries"]

            if args.top and args.top > 0:
                summaries = summaries[: args.top]

            print(
                json.dumps(
                    {
                        "aggregate_concern_summaries": summaries,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return True

        print(
            "\n"
            + format_debug_section_title(
                DEBUG_MECHANISM_PIPELINE_LABEL,
                "Aggregate Concern Summaries",
            )
        )
        print(
            render_aggregate_concern_summaries(
                pipeline,
                top=args.top,
            )
        )
        return True

    if args.show_pairwise_migration_debug:
        pair_reports = _build_pair_reports_for_migration_debug(
            args,
            facts,
            drug_ids,
            rule_dir,
        )
        print(render_pairwise_migration_debug(pair_reports, pipeline))
        return True

    if args.show_aggregates:
        _print_debug_lines(
            DEBUG_MECHANISM_PIPELINE_LABEL,
            "Aggregate Concern Clusters",
            format_aggregate_concerns(list(pipeline.aggregate_concerns)),
        )
        return True

    return False