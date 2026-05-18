"""Print a maintainer-facing PD effect evidence gap report."""

from __future__ import annotations

import argparse
import json

from app.cli import DB_PATH, connect, load_facts
from core.evidence.completeness import build_pd_effect_evidence_gap_report


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


def _format_count_block(title: str, counts: dict[str, int]) -> list[str]:
    lines = [title]

    if not counts:
        lines.append("  none")
        return lines

    for key, value in sorted(counts.items()):
        lines.append(f"  {key}: {value}")

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
    lines.append("Items:")

    for item in report["items"]:
        classification = item["classification"]

        if not show_complete and classification in {
            "high_confidence",
            "moderate_confidence",
        }:
            continue

        lines.append(
            "  "
            f"{item['drug_id']} -> {item['effect_id']}: "
            f"{classification} "
            f"(coverage={item['coverage_status']}, "
            f"confidence={item['confidence_level'] or 'none'}, "
            f"claims={item['claim_count']})"
        )

    return "\n".join(lines)


def main() -> None:
    args = _build_parser().parse_args()

    with connect(DB_PATH) as conn:
        facts = load_facts(conn)

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