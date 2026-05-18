"""Validate a contributor PD effect claim submission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from core.evidence.contributor_claims import (
    contributor_submission_to_validated_draft_claim,
    validate_contributor_pd_effect_submission,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a contributor PD effect claim submission.",
    )
    parser.add_argument(
        "path",
        help="Path to a contributor claim JSON file.",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Print the normalized draft claim if validation passes.",
    )

    return parser


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> None:
    args = _build_parser().parse_args()
    submission = _load_json(Path(args.path))
    errors = validate_contributor_pd_effect_submission(submission)

    if errors:
        print("Invalid contributor claim submission:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)

    if args.draft:
        draft = contributor_submission_to_validated_draft_claim(submission)
        print(json.dumps(draft, indent=2))
        return

    print("Contributor claim submission is valid.")


if __name__ == "__main__":
    main()