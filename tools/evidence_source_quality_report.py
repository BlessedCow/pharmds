"""Print a maintainer-facing evidence source quality report."""

from __future__ import annotations

import argparse
import json

from core.evidence.loader import load_pd_effect_claims, load_sources
from core.evidence.source_quality import (
    build_evidence_source_quality_report,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print an evidence source quality report.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full report as JSON.",
    )
    parser.add_argument(
        "--show-unused",
        action="store_true",
        help="Show unused sources in text output.",
    )
    parser.add_argument(
        "--show-metadata",
        action="store_true",
        help="Show sources missing recommended metadata in text output.",
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
    show_unused: bool = False,
    show_metadata: bool = False,
) -> str:
    lines = [
        "Evidence source quality report",
        "",
        f"Total evidence claims: {report['total_claims']}",
        f"Total source records: {report['total_sources']}",
        f"Referenced source records: {report['referenced_source_count']}",
        f"Unused source records: {report['unused_source_count']}",
        (
            "Missing source references: "
            f"{report['missing_source_reference_count']}"
        ),
        (
            "Sources missing recommended metadata: "
            f"{report['sources_missing_metadata_count']}"
        ),
        "",
    ]

    lines.extend(
        _format_count_block(
            "Source type counts:",
            report["source_type_counts"],
        )
    )
    lines.append("")
    lines.extend(
        _format_count_block(
            "Reliability tier counts:",
            report["reliability_tier_counts"],
        )
    )

    if report["missing_source_references"]:
        lines.append("")
        lines.append("Missing source references:")
        for item in report["missing_source_references"]:
            lines.append(
                f"  {item['claim_id']} -> {item['source_id']}"
            )

    if show_unused:
        lines.append("")
        lines.append("Unused sources:")
        for source in report["unused_sources"]:
            lines.append(
                "  "
                f"{source.get('source_id', 'unknown_source')}: "
                f"{source.get('title', 'untitled')}"
            )

    if show_metadata:
        lines.append("")
        lines.append("Sources missing recommended metadata:")
        for item in report["sources_missing_metadata"]:
            lines.append(
                "  "
                f"{item['source_id']}: "
                f"{', '.join(item['missing_fields'])}"
            )

    return "\n".join(lines)


def main() -> None:
    args = _build_parser().parse_args()
    claims = load_pd_effect_claims()
    sources = load_sources()
    report = build_evidence_source_quality_report(
        claims,
        sources,
    )

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(
        _format_report_text(
            report,
            show_unused=args.show_unused,
            show_metadata=args.show_metadata,
        )
    )


if __name__ == "__main__":
    main()