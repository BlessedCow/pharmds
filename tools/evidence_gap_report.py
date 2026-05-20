"""Print a maintainer-facing PD effect evidence gap report."""

from __future__ import annotations

import argparse
import json
import sqlite3

from app.cli import DB_PATH, connect, load_facts
from core.evidence.completeness import (
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

    return "\n".join(lines)


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