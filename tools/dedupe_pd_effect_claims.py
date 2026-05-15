"""Remove duplicate non-canonical PD effect evidence claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CLAIMS_PATH = Path("data/evidence/pd_effect_claims.json")


def _canonical_claim_id(claim: dict[str, Any]) -> str:
    """Return the canonical claim ID for a PD effect claim."""
    drug_id = claim["subject"]["id"]
    effect_id = claim["object"]["effect_id"]

    return f"claim_{drug_id}_pd_effect_{effect_id}_001"


def main() -> None:
    """Keep canonical PD effect claims and remove duplicate non-canonical IDs."""
    claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))

    canonical_claims = []
    removed_claim_ids = []

    seen_claim_ids = set()

    for claim in claims:
        expected_claim_id = _canonical_claim_id(claim)

        if claim["claim_id"] != expected_claim_id:
            removed_claim_ids.append(claim["claim_id"])
            continue

        if claim["claim_id"] in seen_claim_ids:
            removed_claim_ids.append(claim["claim_id"])
            continue

        seen_claim_ids.add(claim["claim_id"])
        canonical_claims.append(claim)

    canonical_claims.sort(key=lambda item: item["claim_id"])

    CLAIMS_PATH.write_text(
        json.dumps(canonical_claims, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Removed {len(removed_claim_ids)} duplicate/non-canonical claims.")

    for claim_id in removed_claim_ids:
        print(f"- {claim_id}")


if __name__ == "__main__":
    main()