"""Backfill contributor and review governance metadata on PD effect claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.evidence.governance import claim_with_default_governance

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PD_EFFECT_CLAIMS_PATH = (
    PROJECT_ROOT / "data" / "evidence" / "pd_effect_claims.json"
)


def backfill_claim_governance(
    claims: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return claims with default governance metadata filled in."""
    return [claim_with_default_governance(claim) for claim in claims]


def main() -> None:
    claims = json.loads(PD_EFFECT_CLAIMS_PATH.read_text(encoding="utf-8"))
    updated = backfill_claim_governance(claims)
    PD_EFFECT_CLAIMS_PATH.write_text(
        json.dumps(updated, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()