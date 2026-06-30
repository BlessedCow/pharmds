from __future__ import annotations

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from app.cli.commands import handle_evidence_gap_command
from app.cli.domains import (
    _parse_domain_selection,
    filter_rules_for_selected_domains,
)
from app.cli.facts import connect, load_facts
from app.cli.inputs import (
    _collect_drug_inputs,
    _format_unknown_drug_message,
    resolve_drug_ids,
)
from app.cli.pairwise import _build_reports_for_all_pairs
from app.cli.parser import build_parser
from app.cli.render.debug import (
    render_pairwise_migration_debug,
    render_severity_annotations,
    render_severity_comparison,
)
from app.cli.render.plain import (
    render_aggregate_concern_summaries,
    render_aggregate_evidence_summary,
    render_plain_pairwise_details,
    render_plain_regimen_summary,
    render_public_result_summaries,
)
from app.json_output import build_json_payload
from core.evidence.completeness import (
    BACKFILL_PRIORITY_CONFIDENCE,
    BACKFILL_PRIORITY_CONFLICT,
    BACKFILL_PRIORITY_MISSING,
    BACKFILL_PRIORITY_UNDETERMINED,
    GAP_CLASSIFICATIONS,
)
from core.evidence.loader import get_source_by_id
from core.exceptions import UnknownDrugError
from core.mechanisms import (
    mechanism_pipeline_to_json_dict,
    run_mechanism_pipeline,
)
from core.mechanisms.aggregation_debug import format_aggregate_concerns
from core.mechanisms.arbitration_debug import format_arbitration_results
from core.mechanisms.candidate_debug import format_interaction_candidates
from core.mechanisms.debug import (
    DEBUG_MECHANISM_PIPELINE_LABEL,
    DEBUG_PAIRWISE_MIGRATION_LABEL,
    format_debug_section_title,
    format_mechanism_effects,
)
from core.mechanisms.effect_labels import (
    PUBLIC_EFFECT_LABELS,
    effect_display_label,
)
from core.mechanisms.policy_debug import format_policy_results
from core.mechanisms.result_summary import (
    build_public_result_summaries,
)
from core.mechanisms.scoring_debug import format_scored_concerns
from reasoning.combine import build_regimen_summary
from rules.engine import evaluate_all, load_rules

console = Console()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
RULE_DIR = BASE_DIR / "rules" / "rule_defs"

DEFAULT_AGGREGATE_SUMMARY_LIMIT = 5
DEFAULT_PUBLIC_RESULT_SUMMARY_LIMIT = 5


def _sev_rank(sev: str) -> int:
    # Match Severity values: info/caution/major/contraindicated
    order = {"info": 0, "caution": 1, "major": 2, "contraindicated": 3}
    return order.get(sev, 0)


def _is_gap_classification(classification: str) -> bool:
    return classification in GAP_CLASSIFICATIONS


def _format_effect_label_line(effect_id: str | None) -> str | None:
    if not effect_id:
        return None

    label = effect_display_label(effect_id)
    if label == effect_id:
        return None

    return f"  effect_label: {label}"

def _format_effect_value(effect_id: str | None) -> str:
    if not effect_id:
        return "unspecified effect"

    label = effect_display_label(effect_id)
    if label == effect_id:
        return effect_id

    return f"{effect_id} ({label})"

def _format_effect_values(effect_ids: tuple[str, ...]) -> str:
    if not effect_ids:
        return "none"

    return ", ".join(_format_effect_value(effect_id) for effect_id in effect_ids)

def _format_text_values(values: tuple[str, ...]) -> str:
    if not values:
        return "none"

    return ", ".join(values)

def _format_evidence_conflict_reasons(values: tuple[str, ...]) -> str:
    if not values:
        return "none"

    labels = {
        "claim_disagreement": "claim disagreement",
        "confidence": "confidence limitations",
        "coverage": "coverage gaps",
        "source_mismatch": "mixed source types",
    }

    return ", ".join(
        labels.get(value, value.replace("_", " "))
        for value in values
    )

def _format_evidence_source_label(source_id: str) -> str:
    source = get_source_by_id(source_id)

    if not source:
        return source_id

    title = source.get("title") or source_id
    source_type = source.get("source_type")

    if source_type:
        return f"{title} ({source_type})"

    return str(title)


def _format_source_ids(source_ids: tuple[str, ...]) -> str:
    if not source_ids:
        return "none"

    noun = "source" if len(source_ids) == 1 else "sources"
    labels = [
        _format_evidence_source_label(source_id)
        for source_id in source_ids
    ]

    return f"{len(source_ids)} {noun}: " + ", ".join(labels)

def _format_public_effect_text(text: str) -> str:
    out = text

    for effect_id in sorted(PUBLIC_EFFECT_LABELS, key=len, reverse=True):
        effect_label = effect_display_label(effect_id)
        out = out.replace(
            f"{effect_id}-related pharmacodynamic effect",
            _public_pd_effect_phrase(effect_id, effect_label),
        )
        out = out.replace(effect_id, effect_label)

    return out


def _public_pd_effect_phrase(effect_id: str, effect_label: str) -> str:
    if effect_label == effect_id:
        return f"{effect_label}-related pharmacodynamic effect"

    return f"{effect_label} pharmacodynamic effect"

def _format_evidence_gap_item(item: dict) -> str:
    source_types = ", ".join(item.get("source_types") or ["no_source"])
    confidence = item.get("confidence_level") or "none"

    return (
        f"{item['drug_id']} -> {item['effect_id']}: "
        f"{item['classification']} "
        f"(coverage={item['coverage_status']}, "
        f"confidence={confidence}, "
        f"claims={item['claim_count']}, "
        f"source_types={source_types})"
    )

def _format_evidence_backfill_task(task: dict[str, object]) -> str:
    missing_source_types = task.get("missing_source_types") or []
    if not isinstance(missing_source_types, list):
        missing_source_types = []

    missing_sources = ", ".join(str(source) for source in missing_source_types)
    missing_sources = missing_sources or "none"
    confidence = task.get("confidence_level") or task.get("confidence_status")

    return (
        "- "
        f"[{task.get('priority')}] "
        f"{task.get('drug_id')} -> {task.get('effect_id')}: "
        f"{task.get('classification')} "
        f"(coverage={task.get('coverage_status')}, "
        f"confidence={confidence or 'none'}, "
        f"claims={task.get('claim_count')}, "
        f"missing_sources={missing_sources}). "
        f"{task.get('suggested_next_action')}"
    )


def _append_evidence_backfill_task_group(
    lines: list[str],
    title: str,
    grouped_tasks: object,
) -> None:
    lines.extend(["", title])

    if not isinstance(grouped_tasks, dict) or not grouped_tasks:
        lines.append("  none")
        return

    for key, tasks in sorted(grouped_tasks.items()):
        lines.append(f"  {key}:")

        if not isinstance(tasks, list):
            continue

        for task in tasks:
            if isinstance(task, dict):
                lines.append(f"    {_format_evidence_backfill_task(task)}")


def _append_evidence_backfill_plan(
    lines: list[str],
    report: dict,
) -> None:
    backfill_plan = report.get("backfill_plan") or {}
    if not isinstance(backfill_plan, dict):
        return

    tasks = backfill_plan.get("tasks") or []
    lines.extend(["", "Backfill planning report:"])

    if not tasks:
        lines.append("  No backfill tasks found.")
        return

    priority_counts = backfill_plan.get("priority_counts") or {}
    if not isinstance(priority_counts, dict):
        priority_counts = {}

    priority_order = (
        BACKFILL_PRIORITY_MISSING,
        BACKFILL_PRIORITY_CONFLICT,
        BACKFILL_PRIORITY_UNDETERMINED,
        BACKFILL_PRIORITY_CONFIDENCE,
    )

    lines.append(f"  Total backfill tasks: {backfill_plan.get('total_tasks', 0)}")
    lines.extend(["", "Priority counts:"])

    for priority in priority_order:
        count = priority_counts.get(priority, 0)
        if count:
            lines.append(f"  {priority}: {count}")

    lines.extend(["", "Prioritized tasks:"])

    for task in tasks:
        if isinstance(task, dict):
            lines.append(f"  {_format_evidence_backfill_task(task)}")

    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by priority:",
        backfill_plan.get("by_priority"),
    )
    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by PD effect:",
        backfill_plan.get("by_pd_effect"),
    )
    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by drug:",
        backfill_plan.get("by_drug"),
    )
    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by missing source type:",
        backfill_plan.get("by_source_type"),
    )


def _format_public_summary_label(value: object) -> str:
    text = str(value or "").strip()

    if not text:
        return "Not available"

    labels = {
        "high_caution": "High caution",
        "not_available": "Not available",
        "legacy_rule": "Legacy rule",
        "not_applicable": "Not applicable",
    }

    return labels.get(text, text.replace("_", " ").capitalize())


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    drug_names = _collect_drug_inputs(args.drugs, args.file)
    if len(drug_names) < 2:
        raise SystemExit(
            "Provide at least two drugs, or use --file / stdin for a list."
        )

    conn = connect(DB_PATH)

    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
    except UnknownDrugError as e:
        for tok in e.unknown:
            opts = e.suggestions.get(tok, ())
            print(_format_unknown_drug_message(tok, opts), file=sys.stderr)

        print(
            "Tip: common separators such as spaces, hyphens, slashes, and "
            "underscores are treated the same.",
            file=sys.stderr,
        )
        raise SystemExit(2) from e

    patient_flags = {
        "qt_risk": bool(args.qt_risk),
        "bleeding_risk": bool(args.bleeding_risk),
    }
    facts = load_facts(conn, drug_ids, patient_flags)

    if handle_evidence_gap_command(args, facts):
        return 
    
    if (
        args.show_mechanisms
        or args.show_candidates
        or args.show_arbitration
        or args.show_policy
        or args.show_scored
        
        or args.show_aggregates
        or args.show_mechanism_json
        or args.show_severity
        or args.show_severity_comparison
        or args.show_aggregate_evidence
        or args.show_aggregate_summaries
        or args.show_pairwise_migration_debug
    ):
        pipeline = run_mechanism_pipeline(
            drug_ids,
            facts,
            evidence_mode=args.evidence_mode,
        )
        if args.show_mechanism_json:
            payload = mechanism_pipeline_to_json_dict(pipeline)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return

        if args.show_mechanisms:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Normalized MechanismEffect IR",
                )
                + "\n"
            )
            for line in format_mechanism_effects(list(pipeline.effects)):
                print(f"- {line}")

            return

        if args.show_candidates:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Candidate Interaction Patterns",
                )
                + "\n"
            )
            for line in format_interaction_candidates(list(pipeline.candidates)):
                print(f"- {line}")

            return

        if args.show_arbitration:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Arbitration Results",
                )
                + "\n"
            )
            for line in format_arbitration_results(
                list(pipeline.arbitration_results)
            ):
                print(f"- {line}")

            return

        if args.show_policy:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Policy Results",
                )
                + "\n"
            )
            for line in format_policy_results(list(pipeline.policy_results)):
                print(f"- {line}")

            return
        
        if args.show_scored:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Scored Concerns",
                )
                + "\n"
            )
            for line in format_scored_concerns(list(pipeline.scored_concerns)):
                print(f"- {line}")

            return
        
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

            return
        
        if args.show_severity_comparison:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_PAIRWISE_MIGRATION_LABEL,
                    "Severity Comparison",
                )
            )
            print(render_severity_comparison(pipeline))

            return
        
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
                return

            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Aggregate Evidence Summary",
                )
            )
            print(render_aggregate_evidence_summary(pipeline))

            return
        
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
                return

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

            return
        
            if args.show_pairwise_migration_debug:
                rules_all = load_rules(RULE_DIR)
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
                pair_reports = _build_reports_for_all_pairs(
                    facts,
                    hits,
                    templates,
                    drug_ids,
                )

                print(render_pairwise_migration_debug(pair_reports, pipeline))

                return
        if args.show_pairwise_migration_debug:
            rules_all = load_rules(RULE_DIR)
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
            pair_reports = _build_reports_for_all_pairs(
                facts,
                hits,
                templates,
                drug_ids,
            )

            print(render_pairwise_migration_debug(pair_reports, pipeline))

            return
        
        
        if args.show_aggregates:
            print(
                "\n"
                + format_debug_section_title(
                    DEBUG_MECHANISM_PIPELINE_LABEL,
                    "Aggregate Concern Clusters",
                )
                + "\n"
            )
            for line in format_aggregate_concerns(
                list(pipeline.aggregate_concerns)
            ):
                print(f"- {line}")

            return
    selected = _parse_domain_selection(args.domain)

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

    pipeline = run_mechanism_pipeline(
        drug_ids,
        facts,
        evidence_mode=args.evidence_mode,
    )
    public_result_summaries = build_public_result_summaries(pipeline)
        
    # JSON MODE
    if args.format == "json":
        payload = build_json_payload(
            facts=facts,
            reports=pair_reports,
            templates=templates,
            selected_domains=selected,
            input_drug_names=drug_names,
            patient_flags=patient_flags,
            regimen_summary=regimen_summary,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if not pair_reports and not public_result_summaries and not regimen_summary:
        domains = ", ".join(selected)
        print(
            "No rule-based interactions detected in selected domains: "
            f"{domains} (educational scope)."
        )
        return

    # RICH MODE
    if args.format == "rich":

        from app.cli.render.rich import (
            build_summary_rows,
            render_rich_details,
            render_rich_summary,
        )

        print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")

        # Regimen summary (only for 3+ drugs)
        if regimen_summary:
            sev = regimen_summary["overall_severity"].value
            cls = regimen_summary["overall_rule_class"].value
            flags = regimen_summary.get("regimen_flags", [])
            hit_counts = regimen_summary.get("hit_counts", {})
            pd_stacks = regimen_summary.get("pd_stacks", [])
            top_pairs = regimen_summary.get("top_pairs", [])

            lines = [
                f"Overall (regimen): severity={sev} | class={cls}",
                regimen_summary.get("overview", ""),
                "",
                regimen_summary.get("pairwise_summary", ""),
                regimen_summary.get("cumulative_concern_summary", ""),
                "",
                f"Drugs: {regimen_summary.get('n_drugs', 0)}",
                (
                    "Pairs with pairwise hits: "
                    f"{regimen_summary.get('pair_count_with_hits', 0)}"
                ),
                (
                    "Pairwise hits: "
                    f"{hit_counts.get('total', 0)} "
                    f"(PK={hit_counts.get('pk', 0)}, PD={hit_counts.get('pd', 0)})"
                ),
                f"Regimen-wide flags: {len(flags)}",
            ]

            if pd_stacks:
                lines.append("")
                lines.append("Regimen-wide repeated PD concern domains:")
                for stack in pd_stacks[:5]:
                    drug_names = ", ".join(
                        d["drug_name"] for d in stack.get("drugs", [])
                    )
                    lines.append(
                        f"- {stack['label']}: {stack['count']} drugs "
                        f"(max={stack['max_magnitude']})"
                        f" - {drug_names}"
                    )

            if flags:
                lines.append("")
                lines.append("Regimen-wide educational flags:")
                for flag in flags[:5]:
                    lines.append(f"- {flag.get('message', '')}")

            if top_pairs:
                lines.append("")
                lines.append("Pairwise concern highlights:")
                for pair in top_pairs[:3]:
                    lines.append(
                        f"- {pair['drug_1']['name']} + {pair['drug_2']['name']}: "
                        f"{pair['severity']} | {pair['class']} "
                        f"({pair['total_hits']} hits)"
                    )

            console.print(
                Panel(
                    "\n".join(lines),
                    title="Regimen Summary (all drugs)",
                    expand=True,
                )
            )

            print()

        rows = build_summary_rows(facts, pair_reports)
        render_rich_summary(rows, top=args.top or 0)

        detail_reports = (
            pair_reports[: args.top] if args.top and args.top > 0 else pair_reports
        )
        if args.details:
            render_rich_details(
                facts,
                detail_reports,
                templates,
                show_evidence=args.show_evidence,
            )
        return

    # PLAIN MODE
    print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")

    if regimen_summary:
        print(render_plain_regimen_summary(regimen_summary))
        print()

    if public_result_summaries:
        print("Key Interaction Summaries")
        print(render_public_result_summaries(public_result_summaries, top=args.top))
        print()

    if args.details:
        detail_reports = (
            pair_reports[: args.top]
            if args.top and args.top > 0
            else pair_reports
        )
        print(
            render_plain_pairwise_details(
                facts,
                detail_reports,
                templates,
                show_evidence=args.show_evidence,
            )
        )
        print()


if __name__ == "__main__":
    main()

