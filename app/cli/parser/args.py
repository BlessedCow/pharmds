from __future__ import annotations

import argparse

from core.evidence.gating import (
    EVIDENCE_MODE_MODERATE,
    EVIDENCE_MODE_OFF,
    EVIDENCE_MODE_STRICT,
    EVIDENCE_MODE_SUPPORTED,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Educational PK/PD interaction reasoner (rule-based)."
    )
    parser.add_argument(
        "drugs",
        nargs="*",
        help=(
            "Drug names (generic or alias). Example: warfarin fluconazole. "
            "For polypharmacy, prefer --file or piping via stdin."
        ),
    )
    parser.add_argument(
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
    parser.add_argument(
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
    parser.add_argument(
        "--json",
        dest="format",
        action="store_const",
        const="json",
        help="Shortcut for --format json.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help=(
            "Print full per-pair details after the summary in plain "
            "or rich output."
        ),
    )
    parser.add_argument(
        "--show-evidence",
        action="store_true",
        help=(
            "Show compact human-facing evidence summaries in normal "
            "plain output and rich details."
        ),
    )
    parser.add_argument(
        "--show-mechanism-json",
        "--show-mechanism-pipeline",
        dest="show_mechanism_json",
        action="store_true",
        help=(
            "Print the full read-only mechanism pipeline as JSON "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
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
    parser.add_argument(
        "--show-severity",
        action="store_true",
        help=(
            "Show debug severity annotations from the mechanism pipeline."
        ),
    )
    parser.add_argument(
        "--show-severity-comparison",
        action="store_true",
        help=(
            "Show debug comparison between severity annotations "
            "and aggregate concern severity."
        ),
    )
    parser.add_argument(
        "--show-aggregate-evidence",
        action="store_true",
        help=(
            "Show aggregate-level evidence summaries from the mechanism "
            "pipeline and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-aggregate-summaries",
        action="store_true",
        help=(
            "Show joined aggregate concern, severity, and evidence summaries "
            "from the mechanism pipeline and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-pairwise-migration-debug",
        action="store_true",
        help=(
            "Show old pairwise rule reports beside pairwise-shaped "
            "mechanism output and exit."
        ),
    )
    parser.add_argument(
        "--show-evidence-gaps",
        action="store_true",
        help=(
            "Show missing or partial PD effect evidence coverage for the "
            "selected drugs and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-complete-evidence-coverage",
        action="store_true",
        help=(
            "When used with --show-evidence-gaps, also include complete "
            "moderate/high-confidence rows after the gap sections."
        ),
    )
    parser.add_argument(
        "--show-mechanisms",
        action="store_true",
        help=(
            "Print normalized MechanismEffect IR for the selected drugs "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-candidates",
        action="store_true",
        help=(
            "Print inferred interaction candidates from MechanismEffect IR "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-arbitration",
        action="store_true",
        help=(
            "Print arbitration scaffold results from inferred candidates "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-policy",
        action="store_true",
        help=(
            "Print concern policy classifications from arbitration results "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-scored",
        action="store_true",
        help=(
            "Print confidence-scored concern results from policy results "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--show-aggregates",
        action="store_true",
        help=(
            "Print aggregate concern clusters from policy results "
            "and exit without evaluating rules."
        ),
    )
    parser.add_argument(
        "--top",
        type=int,
        default=None,
        help=(
            "Show only the top N rows or aggregate summaries. "
            "For aggregate summaries, omitted uses the default limit. "
            "Use 0 to show all."
        ),
    )
    parser.add_argument(
        "--qt-risk",
        action="store_true",
        help="Patient has QT risk factors (educational flag).",
    )
    parser.add_argument(
        "--bleeding-risk",
        action="store_true",
        help="Patient has bleeding risk factors (educational flag).",
    )
    parser.add_argument(
        "--domain",
        default="all",
        help=(
            "Comma-separated mechanism filters. "
            "Allowed: cyp, ugt, pgp, bcrp, oatp, pd, pk (alias), all. "
            "Examples: --domain cyp  |  --domain ugt  |  --domain pd  |  "
            "--domain cyp,pd"
        ),
    )
    return parser