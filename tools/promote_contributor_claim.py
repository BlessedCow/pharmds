"""Promote a contributor PD effect claim submission to an approved claim."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from core.evidence.claim_workflow import (
    contributor_submission_to_approved_claim,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and promote a contributor PD effect claim submission "
            "to an approved active evidence claim."
        ),
    )
    parser.add_argument(
        "path",
        help="Path to a contributor claim JSON file.",
    )
    parser.add_argument(
        "--reviewed-by",
        required=True,
        help="Reviewer ID or role.",
    )
    parser.add_argument(
        "--reviewed-at",
        required=True,
        help="Review date, for example 2026-05-18.",
    )
    parser.add_argument(
        "--out",
        help="Optional output path for the approved claim JSON.",
    )

    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    args = _build_parser().parse_args()
    submission = _load_json(Path(args.path))
    approved = contributor_submission_to_approved_claim(
        submission,
        reviewed_by=args.reviewed_by,
        reviewed_at=args.reviewed_at,
    )

    if args.out:
        _write_json(Path(args.out), approved)
        print(f"Wrote approved claim to {args.out}")
        return

    print(json.dumps(approved, indent=2))


if __name__ == "__main__":
    main()