"""Print a maintainer-facing PD effect evidence gap report."""

from __future__ import annotations

import argparse
import json
import sqlite3

from app.cli import DB_PATH, connect, load_facts
from core.evidence.completeness import (
    BACKFILL_PRIORITY_CONFIDENCE,
    BACKFILL_PRIORITY_CONFLICT,
    BACKFILL_PRIORITY_MISSING,
    BACKFILL_PRIORITY_UNDETERMINED,
    GAP_CLASSIFICATIONS,
    build_pd_effect_evidence_gap_report,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print a PD effect evidence gap report.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full report as JSON.",
    )
    parser.add_argument(
        "--show-complete",
        action="store_true",
        help="Include complete/moderate/high-confidence rows in text output.",
    )

    return parser


def _all_drug_ids(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT id
        FROM drug
        ORDER BY id
        """
    ).fetchall()

    return [row["id"] for row in rows]


def _format_count_block(title: str, counts: dict[str, int]) -> list[str]:
    lines = [title]

    if not counts:
        lines.append("  none")
        return lines

    for key, value in sorted(counts.items()):
        lines.append(f"  {key}: {value}")

    return lines


def _is_gap_classification(classification: str) -> bool:
    return classification in GAP_CLASSIFICATIONS


def _format_item(item: dict) -> str:
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


def _format_grouped_items(
    title: str,
    grouped_items: dict[str, list[dict]],
) -> list[str]:
    lines = [title]

    if not grouped_items:
        lines.append("  none")
        return lines

    for key, items in sorted(grouped_items.items()):
        lines.append(f"  {key}:")
        for item in items:
            lines.append(f"    - {_format_item(item)}")

    return lines


def _format_report_text(
    report: dict,
    *,
    show_complete: bool = False,
) -> str:
    lines = [
        "PD effect evidence gap report",
        "",
        f"Total ontology PD effects: {report['total_pd_effects']}",
        f"Missing/partial evidence rows: {report['gap_count']}",
        "",
    ]
    lines.extend(
        _format_count_block(
            "Coverage counts:",
            report["coverage_counts"],
        )
    )
    lines.append("")
    lines.extend(
        _format_count_block(
            "Confidence counts:",
            report["confidence_counts"],
        )
    )
    lines.append("")
    lines.extend(
        _format_count_block(
            "Classification counts:",
            report["classification_counts"],
        )
    )
    lines.append("")
    lines.extend(
        _format_grouped_items(
            "Grouped by PD effect:",
            report["gaps_by_pd_effect"],
        )
    )
    lines.append("")
    lines.extend(
        _format_grouped_items(
            "Grouped by drug:",
            report["gaps_by_drug"],
        )
    )
    lines.append("")
    lines.extend(
        _format_grouped_items(
            "Grouped by source type:",
            report["gaps_by_source_type"],
        )
    )

    if show_complete:
        lines.extend(["", "Complete/moderate/high rows:"])
        complete_items = [
            item
            for item in report["items"]
            if not _is_gap_classification(item["classification"])
        ]

        if not complete_items:
            lines.append("  none")
        else:
            for item in complete_items:
                lines.append(f"  - {_format_item(item)}")
        
    backfill_lines = _format_backfill_plan(report)
    if backfill_lines:
        lines.append("")
        lines.extend(backfill_lines)

    return "\n".join(lines)

def _format_backfill_plan(report: dict[str, object]) -> list[str]:
    """Format prioritized evidence backfill tasks for maintainers."""
    backfill_plan = report.get("backfill_plan") or {}
    if not isinstance(backfill_plan, dict):
        return []

    tasks = backfill_plan.get("tasks") or []
    if not tasks:
        return ["Backfill planning report:", "  No backfill tasks found."]

    priority_counts = backfill_plan.get("priority_counts") or {}
    priority_order = (
        BACKFILL_PRIORITY_MISSING,
        BACKFILL_PRIORITY_CONFLICT,
        BACKFILL_PRIORITY_UNDETERMINED,
        BACKFILL_PRIORITY_CONFIDENCE,
    )

    lines = [
        "Backfill planning report:",
        f"  Total backfill tasks: {backfill_plan.get('total_tasks', 0)}",
    ]

    for priority in priority_order:
        count = priority_counts.get(priority, 0)
        if count:
            lines.append(f"  {priority}: {count}")

    lines.append("  Prioritized tasks:")

    for task in tasks:
        if not isinstance(task, dict):
            continue

        missing_source_types = task.get("missing_source_types") or []
        missing_sources = ", ".join(missing_source_types) or "none"
        lines.append(
            "    - "
            f"[{task.get('priority')}] "
            f"{task.get('drug')} -> {task.get('pd_effect')}: "
            f"{task.get('coverage_status')} evidence, "
            f"confidence={task.get('confidence')}, "
            f"conflict={task.get('conflict_status')}, "
            f"claims={task.get('claim_count')}, "
            f"missing_sources={missing_sources}. "
            f"{task.get('suggested_next_action')}"
        )

    return lines

def main() -> None:
    args = _build_parser().parse_args()

    with connect(DB_PATH) as conn:
        drug_ids = _all_drug_ids(conn)
        facts = load_facts(conn, drug_ids, {})

    report = build_pd_effect_evidence_gap_report(facts)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(
        _format_report_text(
            report,
            show_complete=args.show_complete,
        )
    )


if __name__ == "__main__":
    main()