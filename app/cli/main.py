from __future__ import annotations

from pathlib import Path

from rich.console import Console

from app.cli.commands import (
    handle_evidence_gap_command,
    handle_mechanism_debug_command,
    handle_output_command,
)
from app.cli.parser import build_parser
from app.cli.runtime import (
    build_cli_pair_reports,
    build_cli_session,
    build_cli_summaries,
    resolve_aggregate_summary_limit,
)
from core.evidence.completeness import (
    BACKFILL_PRIORITY_CONFIDENCE,
    BACKFILL_PRIORITY_CONFLICT,
    BACKFILL_PRIORITY_MISSING,
    BACKFILL_PRIORITY_UNDETERMINED,
    GAP_CLASSIFICATIONS,
)
from core.evidence.loader import get_source_by_id
from core.mechanisms.effect_labels import (
    PUBLIC_EFFECT_LABELS,
    effect_display_label,
)

console = Console()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
RULE_DIR = BASE_DIR / "rules" / "rule_defs"

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

    return ", ".join(labels.get(value, value.replace("_", " ")) for value in values)


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
    labels = [_format_evidence_source_label(source_id) for source_id in source_ids]

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

    session = build_cli_session(args, db_path=DB_PATH)

    drug_names = session.drug_names
    drug_ids = session.drug_ids
    patient_flags = session.patient_flags
    facts = session.facts

    if handle_evidence_gap_command(args, facts):
        return

    if handle_mechanism_debug_command(
        args,
        facts,
        drug_ids,
        rule_dir=RULE_DIR,
    ):
        return

    selected, templates, pair_reports = build_cli_pair_reports(
        args,
        facts=facts,
        drug_ids=drug_ids,
        rule_dir=RULE_DIR,
    )
    
    regimen_summary, pipeline, public_result_summaries = build_cli_summaries(
        args,
        facts=facts,
        drug_ids=drug_ids,
        pair_reports=pair_reports,
    )
    aggregate_summary_limit = resolve_aggregate_summary_limit(args)

    handle_output_command(
        args,
        facts=facts,
        pair_reports=pair_reports,
        templates=templates,
        selected=selected,
        drug_names=drug_names,
        patient_flags=patient_flags,
        regimen_summary=regimen_summary,
        public_result_summaries=public_result_summaries,
        console=console,
        aggregate_summary_limit=aggregate_summary_limit,
    )


if __name__ == "__main__":
    main()
