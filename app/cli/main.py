from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from app.cli.facts import connect, load_facts
from app.cli.inputs import (
    _collect_drug_inputs,
    _format_unknown_drug_message,
    resolve_drug_ids,
)
from app.cli.domains import (
    _parse_domain_selection,
    filter_rules_for_selected_domains,
)
from app.cli.pairwise import _build_reports_for_all_pairs
from app.json_output import build_json_payload
from core.evidence.completeness import (
    BACKFILL_PRIORITY_CONFIDENCE,
    BACKFILL_PRIORITY_CONFLICT,
    BACKFILL_PRIORITY_MISSING,
    BACKFILL_PRIORITY_UNDETERMINED,
    GAP_CLASSIFICATIONS,
    build_pd_effect_evidence_gap_report,
)
from core.evidence.gating import (
    EVIDENCE_MODE_MODERATE,
    EVIDENCE_MODE_OFF,
    EVIDENCE_MODE_STRICT,
    EVIDENCE_MODE_SUPPORTED,
)
from core.evidence.human_rendering import (
    build_human_evidence_lines_for_rule_hit,
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
    DEBUG_OLD_PAIRWISE_LABEL,
    DEBUG_PAIRWISE_MIGRATION_LABEL,
    format_debug_section_title,
    format_mechanism_effects,
    format_old_pairwise_rule_reports,
    format_pairwise_mechanism_concerns,
)
from core.mechanisms.effect_labels import (
    PUBLIC_EFFECT_LABELS,
    effect_display_label,
)
from core.mechanisms.pairwise_adapter import adapt_mechanism_pipeline_to_pairwise
from core.mechanisms.policy_debug import format_policy_results
from core.mechanisms.result_summary import (
    ResultSummary,
    build_public_result_summaries,
)
from core.mechanisms.scoring_debug import format_scored_concerns
from core.models import Facts
from reasoning.combine import build_pair_reports, build_regimen_summary
from reasoning.explain import render_explanation, render_rationale
from reasoning.rationale import action_rationale, severity_rationale
from rules.engine import evaluate_all, load_rules, rule_mechanisms

console = Console()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
RULE_DIR = BASE_DIR / "rules" / "rule_defs"

DEFAULT_AGGREGATE_SUMMARY_LIMIT = 5
DEFAULT_PUBLIC_RESULT_SUMMARY_LIMIT = 5
PLAIN_EMPTY_DETAILS_MESSAGE = "No pairwise detail rows to display."
PLAIN_AGGREGATE_HINT_MESSAGE = (
    "Use --show-aggregate-summaries to inspect mechanism-level aggregate concerns."
)


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

def render_evidence_gap_report(
    report: dict,
    *,
    show_complete: bool = False,
) -> str:
    """Render selected-drug PD evidence coverage gaps for CLI output."""
    lines = [
        "PD Effect Evidence Gaps",
        "",
        f"Total PD effects checked: {report['total_pd_effects']}",
        f"Missing/partial evidence rows: {report['gap_count']}",
        "",
        "Coverage counts:",
    ]

    for key, count in sorted(report["coverage_counts"].items()):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Confidence counts:"])
    for key, count in sorted(report["confidence_counts"].items()):
        lines.append(f"  {key}: {count}")

    def add_group(title: str, group: dict[str, list[dict]]) -> None:
        lines.extend(["", title])
        if not group:
            lines.append("  none")
            return

        for key, items in sorted(group.items()):
            visible_items = [
                item
                for item in items
                if show_complete
                or _is_gap_classification(item["classification"])
            ]
            if not visible_items:
                continue

            lines.append(f"  {key}:")
            for item in visible_items:
                lines.append(f"    - {_format_evidence_gap_item(item)}")

    add_group("Grouped by PD effect:", report["gaps_by_pd_effect"])
    add_group("Grouped by drug:", report["gaps_by_drug"])
    add_group("Grouped by source type:", report["gaps_by_source_type"])

    if show_complete:
        lines.extend(["", "Complete/moderate/high rows:"])
        complete_items = [
            item
            for item in report["items"]
            if not _is_gap_classification(item["classification"])
        ]
        if not complete_items:
            lines.append("  none")
        for item in complete_items:
            lines.append(f"  - {_format_evidence_gap_item(item)}")

    _append_evidence_backfill_plan(lines, report)

    return "\n".join(lines)

def render_severity_annotations(severity_annotations):
    """Render mechanism severity annotations for CLI debug output."""
    if not severity_annotations:
        return "No severity annotations."

    lines = []

    for annotation in severity_annotations:
        scored = annotation.scored

        lines.append(
            f"- {scored.precipitant_drug} + {scored.object_drug}"
            f" | effect={scored.effect_id}"
            f" | concern={scored.policy_concern}"
        )
        lines.append(f"  candidate_type: {scored.candidate_type}")
        lines.append(f"  confidence: {scored.confidence}")
        lines.append(f"  preliminary_severity: {annotation.preliminary_severity}")
        lines.append(f"  severity_reason: {annotation.severity_reason}")
        lines.append(f"  explanation: {scored.explanation}")

        if scored.related_effects:
            related_effects = sorted(
                {
                    effect.strip()
                    for effect_group in scored.related_effects
                    for effect in effect_group.split(",")
                    if effect.strip()
                }
            )
            lines.append(
                "  related_effects: "
                + ", ".join(related_effects)
            )

        if scored.related_targets:
            lines.append(
                "  related_targets: "
                + ", ".join(scored.related_targets)
            )

        lines.append("")

    return "\n".join(lines).rstrip()

def render_aggregate_evidence_summary(pipeline):
    """Render aggregate evidence summaries for CLI debug output."""
    if not pipeline.aggregate_evidence_summaries:
        return "No aggregate evidence summaries."

    lines = []

    for summary in pipeline.aggregate_evidence_summaries:
        aggregate = summary.aggregate
        drugs = ", ".join(aggregate.drugs)
        effect_id = aggregate.effect_id or aggregate.anchor

        lines.append("")
        lines.append(
            f"- {aggregate.aggregate_type}: {aggregate.anchor}"
            f" | policy_concern={aggregate.policy_concern}"
            f" | drugs={drugs}"
            f" | effect={_format_effect_value(effect_id)}"
        )
        lines.append(
            "  overall_evidence_status: "
            + str(summary.overall_evidence_status)
        )
        lines.append(
            "  evidence_trace_count: "
            + str(summary.evidence_trace_count)
        )

        lines.append(
            "  evidence_trace_types: "
            + _format_text_values(summary.evidence_trace_types)
        )
        lines.append(
            "  evidence_effect_ids: "
            + _format_effect_values(summary.evidence_effect_ids)
        )

        lines.append(
            "  evidence_statuses: "
            + _format_text_values(summary.evidence_statuses)
        )

        lines.append(
            "  evidence_gap_count: "
            + str(summary.evidence_gap_count)
        )
        lines.append(
            "  evidence_claim_count: "
            + str(summary.evidence_claim_count)
        )

        lines.append(
            "  evidence_sources: "
            + _format_source_ids(summary.evidence_source_ids)
        )
        lines.append(
            "  evidence_source_types: "
            + _format_text_values(summary.evidence_source_types)
        )
        lines.append(
            "  evidence_conflict_reasons: "
            + _format_evidence_conflict_reasons(
                summary.evidence_conflict_reasons
            )
        )
        lines.append(
            "  member_without_evidence_trace_count: "
            + str(summary.member_without_evidence_trace_count)
        )

    return "\n".join(lines)

def render_aggregate_concern_summaries(
    pipeline,
    top: int | None = DEFAULT_AGGREGATE_SUMMARY_LIMIT,
):
    """Render joined aggregate concern summaries for CLI debug output."""
    summaries = list(pipeline.aggregate_concern_summaries)

    if not summaries:
        return "No aggregate concern summaries."

    if top is not None and top > 0:
        visible_summaries = summaries[:top]
    else:
        visible_summaries = summaries

    lines = []

    for summary in visible_summaries:
        aggregate = summary.aggregate
        severity = summary.severity_annotation
        evidence = summary.evidence_summary
        drugs = ", ".join(aggregate.drugs) if aggregate.drugs else "none"
        targets = ", ".join(aggregate.targets) if aggregate.targets else "none"
        effect_id = aggregate.effect_id or aggregate.anchor

        lines.append("")
        lines.append(f"- {aggregate.aggregate_type}: {aggregate.anchor}")
        lines.append(f"  drugs: {drugs}")
        lines.append(f"  effect: {_format_effect_value(effect_id)}")
        lines.append(f"  targets: {targets}")
        lines.append(f"  policy_concern: {aggregate.policy_concern}")

        if severity:
            lines.append(
                "  strongest_preliminary_severity: "
                + str(severity.strongest_preliminary_severity)
            )
        else:
            lines.append("  strongest_preliminary_severity: none")

        if evidence:
            evidence_status = evidence.overall_evidence_status
            evidence_gap_count = evidence.evidence_gap_count
            evidence_claim_count = evidence.evidence_claim_count
            evidence_source_ids = evidence.evidence_source_ids
        else:
            evidence_status = "none"
            evidence_gap_count = 0
            evidence_claim_count = 0
            evidence_source_ids = ()

        lines.append(f"  evidence_status: {evidence_status}")
        lines.append(f"  evidence_gap_count: {evidence_gap_count}")
        lines.append(f"  evidence_claim_count: {evidence_claim_count}")
        lines.append(
            "  evidence_source_count: "
            + str(len(evidence_source_ids))
        )
        lines.append(
            "  evidence_sources: "
            + _format_source_ids(evidence_source_ids)
        )

        if summary.patient_risk_modifiers:
            lines.append(
                "  patient_risk_modifiers: "
                + ", ".join(summary.patient_risk_modifiers)
            )
        else:
            lines.append("  patient_risk_modifiers: none")

        if summary.risk_context:
            lines.append("  risk_context: " + summary.risk_context)

        lines.append(
            "  evidence_conflict_level: "
            + str(summary.evidence_conflict_level)
        )

        if summary.evidence_conflict_message:
            lines.append(
                "  evidence_conflict_message: "
                + summary.evidence_conflict_message
            )

        if summary.evidence_conflict_source_ids:
            lines.append(
                "  evidence_conflict_source_ids: "
                + ", ".join(summary.evidence_conflict_source_ids)
            )

        if summary.evidence_conflict_trace_types:
            lines.append(
                "  evidence_conflict_trace_types: "
                + ", ".join(summary.evidence_conflict_trace_types)
            )

        if summary.evidence_conflict_reasons:
            lines.append(
                "  evidence_conflict_reasons: "
                + _format_evidence_conflict_reasons(
                    summary.evidence_conflict_reasons
                )
            )
        
        if summary.narrative:
            lines.append(
                "  narrative: "
                + _format_public_effect_text(summary.narrative)
            )

    hidden_count = len(summaries) - len(visible_summaries)
    if hidden_count > 0:
        noun = "summary" if hidden_count == 1 else "summaries"
        lines.append("")
        lines.append(
            f"... {hidden_count} aggregate concern {noun} hidden. "
            "Use --top 0 to show all."
        )

    return "\n".join(lines)

def render_pairwise_migration_debug(pair_reports, pipeline) -> str:
    """Render old pairwise output beside pairwise-shaped mechanism output."""
    mechanism_concerns = adapt_mechanism_pipeline_to_pairwise(pipeline)

    lines = [
        DEBUG_PAIRWISE_MIGRATION_LABEL,
        "",
        format_debug_section_title(
            DEBUG_OLD_PAIRWISE_LABEL,
            "Rule Reports",
        ),
    ]

    old_lines = format_old_pairwise_rule_reports(list(pair_reports))
    if old_lines:
        lines.extend(f"- {line}" for line in old_lines)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            format_debug_section_title(
                DEBUG_MECHANISM_PIPELINE_LABEL,
                "Pairwise Adapter Concerns",
            ),
        ]
    )

    mechanism_lines = format_pairwise_mechanism_concerns(mechanism_concerns)
    if mechanism_lines:
        lines.extend(f"- {line}" for line in mechanism_lines)
    else:
        lines.append("- none")

    return "\n".join(lines)

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

def render_public_result_summaries(
    summaries: list[ResultSummary],
    top: int | None = DEFAULT_PUBLIC_RESULT_SUMMARY_LIMIT,
) -> str:
    """Render public result summaries for default plain CLI output."""
    if not summaries:
        return "No key interaction summaries."

    if top is not None and top > 0:
        visible_summaries = summaries[:top]
    else:
        visible_summaries = summaries

    hidden_count = len(summaries) - len(visible_summaries)
    lines = []

    for summary in visible_summaries:
        drugs = ", ".join(summary.drugs) if summary.drugs else "none"

        lines.append(f"- {summary.title}")
        lines.append(f"  drugs: {drugs}")
        lines.append(
            f"  concern_type: {_format_public_summary_label(summary.concern_type)}"
        )
        lines.append(
            f"  severity: {_format_public_summary_label(summary.severity_label)}"
        )
        lines.append(
            f"  evidence: {_format_public_summary_label(summary.evidence_label)}"
        )
        lines.append(f"  explanation: {summary.explanation}")
        lines.append("")

    if hidden_count > 0:
        noun = "summary" if hidden_count == 1 else "summaries"
        lines.append(
            f"... {hidden_count} key interaction {noun} hidden. "
            "Use --top 0 to show all."
        )

    return "\n".join(lines).rstrip()

def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def render_plain_regimen_summary(regimen_summary: dict) -> str:
    """Render regimen-level summary for default plain CLI output."""
    if not regimen_summary:
        return ""

    hit_counts = regimen_summary.get("hit_counts", {})
    flags = regimen_summary.get("regimen_flags", [])
    pd_stacks = regimen_summary.get("pd_stacks", [])
    top_pairs = regimen_summary.get("top_pairs", [])

    lines = [
        "Regimen Summary",
        f"overall_severity: {_enum_value(regimen_summary.get('overall_severity'))}",
        f"overall_class: {_enum_value(regimen_summary.get('overall_rule_class'))}",
    ]

    overview = regimen_summary.get("overview")
    if overview:
        lines.append(f"overview: {overview}")

    pairwise_summary = regimen_summary.get("pairwise_summary")
    if pairwise_summary:
        lines.append(f"pairwise_section: {pairwise_summary}")

    cumulative_summary = regimen_summary.get("cumulative_concern_summary")
    if cumulative_summary:
        lines.append(f"regimen_wide_section: {cumulative_summary}")

    lines.extend(
        [
            f"drugs: {regimen_summary.get('n_drugs', 0)}",
            (
                "pairs_with_pairwise_hits: "
                f"{regimen_summary.get('pair_count_with_hits', 0)}"
            ),
            (
                "pairwise_hits: "
                f"{hit_counts.get('total', 0)} "
                f"(PK={hit_counts.get('pk', 0)}, PD={hit_counts.get('pd', 0)})"
            ),
            f"regimen_wide_flags: {len(flags)}",
        ]
    )

    if flags:
        lines.append("")
        lines.append("Regimen-wide educational flags:")
        for flag in flags[:5]:
            lines.append(f"- {flag.get('message', '')}")

    if pd_stacks:
        lines.append("")
        lines.append("Regimen-wide repeated PD concern domains:")
        for stack in pd_stacks[:5]:
            drug_names = ", ".join(
                drug["drug_name"] for drug in stack.get("drugs", [])
            )
            lines.append(
                f"- {stack['label']}: {stack['count']} drugs "
                f"(max={stack['max_magnitude']}) - {drug_names}"
            )

    if top_pairs:
        lines.append("")
        lines.append("Pairwise concern highlights:")
        for pair in top_pairs[:3]:
            lines.append(
                f"- {pair['drug_1']['name']} + {pair['drug_2']['name']}: "
                f"{pair['severity']} | {pair['class']} "
                f"({pair['total_hits']} hits)"
            )

    return "\n".join(lines)

def render_plain_pairwise_details(
    facts: Facts,
    pair_reports,
    templates: dict[str, str],
    *,
    show_evidence: bool = False,
) -> str:
    """Render full pairwise details for plain CLI output."""
    reports = list(pair_reports)
    lines: list[str] = ["Pairwise Details"]

    if not reports:
        lines.append(PLAIN_EMPTY_DETAILS_MESSAGE)
        lines.append(PLAIN_AGGREGATE_HINT_MESSAGE)
        return "\n".join(lines)

    for rep in reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name

        lines.append("=" * 80)
        lines.append(f"{d1} + {d2}")
        lines.append(
            f"Overall: severity={rep.overall_severity.value} | "
            f"class={rep.overall_rule_class.value}"
        )
        lines.append("")

        if rep.pk_hits:
            lines.append("PK section (directional):")
            if rep.pk_summary:
                lines.append(f"PK summary: {rep.pk_summary}")
            for h in rep.pk_hits:
                a_drug = facts.drugs[h.inputs["A"]].generic_name
                b_drug = facts.drugs[h.inputs["B"]].generic_name
                lines.append(f"- [{h.severity.value} | {h.rule_class.value}] {h.name}")
                lines.append(f"  Affected: {a_drug} | Interacting: {b_drug}")

                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    ex = render_explanation(tmpl, facts, h)
                    lines.append(f"  Explanation: {ex}")

                rat = render_rationale(facts, h)
                if rat:
                    lines.append("  Rationale:")
                    for line in rat.splitlines():
                        lines.append(f"   {line}")

                lines.append("  Severity rationale:")
                lines.append(f"   {severity_rationale(h.severity)}")

                lines.append("  Action rationale:")
                lines.append(f"   {action_rationale(h.rule_class)}")

                if h.actions:
                    lines.append("  Suggested actions:")
                    for action in h.actions:
                        lines.append(f"   - {action}")

                lines.append("")

        if facts.pd_effects:
            lines.append("PD effects (by drug):")
            for drug_id, effects in facts.pd_effects.items():
                effect_ids = sorted({effect.effect_id for effect in effects})
                lines.append(f"- {drug_id}: {', '.join(effect_ids)}")
            lines.append("")

        if rep.pd_hits:
            lines.append("PD section (shared domain):")
            for h in rep.pd_hits:
                lines.append(f"- [{h.severity.value} | {h.rule_class.value}] {h.name}")

                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    ex = render_explanation(tmpl, facts, h)
                    lines.append(f"  Explanation: {ex}")

                rat = render_rationale(facts, h)
                if rat:
                    lines.append("  Rationale:")
                    for line in rat.splitlines():
                        lines.append(f"   {line}")

                lines.append("  Severity rationale:")
                lines.append(f"   {severity_rationale(h.severity)}")

                lines.append("  Action rationale:")
                lines.append(f"   {action_rationale(h.rule_class)}")

                if h.actions:
                    lines.append("  Suggested actions:")
                    for action in h.actions:
                        lines.append(f"   - {action}")

                if show_evidence:
                    evidence_lines = build_human_evidence_lines_for_rule_hit(
                        facts,
                        h,
                    )
                    if evidence_lines:
                        lines.append("  Evidence:")
                        for line in evidence_lines:
                            lines.append(f"   {line}")

                lines.append("")

        refs: list[dict[str, str]] = []
        for h in (rep.pk_hits or []) + (rep.pd_hits or []):
            refs.extend(h.references)

        uniq = {
            (r.get("source", ""), r.get("citation", ""), r.get("url", ""))
            for r in refs
        }
        if uniq:
            lines.append("References (rule-level):")
            for source, citation, url in sorted(uniq):
                if url:
                    lines.append(f"- {source}: {citation} ({url})")
                else:
                    lines.append(f"- {source}: {citation}")
            lines.append("")

    lines.append("=" * 80)
    lines.append(
        "Footer: This output is an educational mechanistic explanation. "
        "Verify with primary sources."
    )

    return "\n".join(lines).rstrip()

def render_severity_comparison(pipeline):
    """Render comparison between aggregate concerns and aggregate severity."""
    if not pipeline.aggregate_severity_annotations:
        return "No aggregate severity annotations."

    lines = []

    for annotation in pipeline.aggregate_severity_annotations:
        aggregate = annotation.aggregate
        drugs = ", ".join(aggregate.drugs)
        effect_id = aggregate.effect_id or aggregate.anchor
        effect_label_line = _format_effect_label_line(effect_id)

        lines.append("")
        lines.append(
            f"- {aggregate.aggregate_type}: {aggregate.anchor}"
            f" | policy_concern={aggregate.policy_concern}"
            f" | drugs={drugs}"
            f" | effect={effect_id}"
        )
        if effect_label_line:
            lines.append(effect_label_line)
        lines.append(
            "  strongest_preliminary_severity: "
            + str(annotation.strongest_preliminary_severity)
        )

        if annotation.contributing_preliminary_severities:
            lines.append(
                "  contributing_preliminary_severities: "
                + ", ".join(annotation.contributing_preliminary_severities)
            )
        else:
            lines.append("  contributing_preliminary_severities: none")

        if annotation.severity_reasons:
            lines.append(
                "  severity_reason: "
                + " | ".join(annotation.severity_reasons)
            )
        else:
            lines.append("  severity_reason: no matching severity annotation")

    return "\n".join(lines)

def main() -> None:
    p = argparse.ArgumentParser(
        description="Educational PK/PD interaction reasoner (rule-based)."
    )
    p.add_argument(
        "drugs",
        nargs="*",
        help=(
            "Drug names (generic or alias). Example: warfarin fluconazole. "
            "For polypharmacy, prefer --file or piping via stdin."
        ),
    )
    p.add_argument(
        "-f",
        "--file",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Read drug names from a file (repeatable). One drug per line, "
            "or comma/whitespace-separated. Use '-' to read from stdin. "
            "If no drugs are provided and stdin is piped, stdin is read automatically."
        ),
    )
    p.add_argument(
        "--format",
        choices=("plain", "rich", "json"),
        default="plain",
        help=(
            "Output format.\n"
            "Use 'rich' for colored tables/panels (requires rich).\n "
            "Use 'json' for structured output.\n "
            "Default: plain."
        ),
    )
    p.add_argument(
        "--json",
        dest="format",
        action="store_const",
        const="json",
        help="Shortcut for --format json.",
    )
    p.add_argument(
        "--details",
        action="store_true",
        help=(
            "Print full per-pair details after the summary in plain "
            "or rich output."
        ),
    )
    p.add_argument(
        "--show-evidence",
        action="store_true",
        help=(
            "Show compact human-facing evidence summaries in normal "
            "plain output and rich details."
        ),
    )
    p.add_argument(
        "--show-mechanism-json",
        "--show-mechanism-pipeline",
        dest="show_mechanism_json",
        action="store_true",
        help=(
            "Print the full read-only mechanism pipeline as JSON "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--evidence-mode",
        choices=[
            EVIDENCE_MODE_OFF,
            EVIDENCE_MODE_SUPPORTED,
            EVIDENCE_MODE_MODERATE,
            EVIDENCE_MODE_STRICT,
        ],
        default=EVIDENCE_MODE_OFF,
        help=(
            "Evidence gating mode for mechanism pipeline PD effects. "
            "Use 'off' for default behavior, 'supported' to require "
            "supporting evidence, 'moderate' to require moderate/high "
            "synthesized confidence, or 'strict' to require high-confidence "
            "cleanly supported evidence."
        ),
    )
    p.add_argument(
        "--show-severity",
        action="store_true",
        help=(
            "Show debug severity annotations from the mechanism pipeline."
        ),
    )
    p.add_argument(
        "--show-severity-comparison",
        action="store_true",
        help=(
            "Show debug comparison between severity annotations "
            "and aggregate concern severity."
        ),
    )
    p.add_argument(
        "--show-aggregate-evidence",
        action="store_true",
        help=(
            "Show aggregate-level evidence summaries from the mechanism "
            "pipeline and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-aggregate-summaries",
        action="store_true",
        help=(
            "Show joined aggregate concern, severity, and evidence summaries "
            "from the mechanism pipeline and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-pairwise-migration-debug",
        action="store_true",
        help=(
            "Show old pairwise rule reports beside pairwise-shaped "
            "mechanism output and exit."
        ),
    )
    p.add_argument(
        "--show-evidence-gaps",
        action="store_true",
        help=(
            "Show missing or partial PD effect evidence coverage for the "
            "selected drugs and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-complete-evidence-coverage",
        action="store_true",
        help=(
            "When used with --show-evidence-gaps, also include complete "
            "moderate/high-confidence rows after the gap sections."
        ),
    )
    p.add_argument(
        "--show-mechanisms",
        action="store_true",
        help=(
            "Print normalized MechanismEffect IR for the selected drugs "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-candidates",
        action="store_true",
        help=(
            "Print inferred interaction candidates from MechanismEffect IR "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-arbitration",
        action="store_true",
        help=(
            "Print arbitration scaffold results from inferred candidates "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-policy",
        action="store_true",
        help=(
            "Print concern policy classifications from arbitration results "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-scored",
        action="store_true",
        help=(
            "Print confidence-scored concern results from policy results "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--show-aggregates",
        action="store_true",
        help=(
            "Print aggregate concern clusters from policy results "
            "and exit without evaluating rules."
        ),
    )
    p.add_argument(
        "--top",
        type=int,
        default=None,
        help=(
            "Show only the top N rows or aggregate summaries. "
            "For aggregate summaries, omitted uses the default limit. "
            "Use 0 to show all."
        ),
    )
    p.add_argument(
        "--qt-risk",
        action="store_true",
        help="Patient has QT risk factors (educational flag).",
    )
    p.add_argument(
        "--bleeding-risk",
        action="store_true",
        help="Patient has bleeding risk factors (educational flag).",
    )
    p.add_argument(
        "--domain",
        default="all",
        help=(
            "Comma-separated mechanism filters. "
            "Allowed: cyp, ugt, pgp, bcrp, oatp, pd, pk (alias), all. "
            "Examples: --domain cyp  |  --domain ugt  |  --domain pd  |  "
            "--domain cyp,pd"
        ),
    )
    args = p.parse_args()

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

    if args.show_evidence_gaps:
        report = build_pd_effect_evidence_gap_report(facts)

        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True))
            return

        print(
            render_evidence_gap_report(
                report,
                show_complete=args.show_complete_evidence_coverage,
            )
        )
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

        from app.render import (
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

