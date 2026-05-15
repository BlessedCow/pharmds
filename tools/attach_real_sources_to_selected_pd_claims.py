"""Attach real source records to selected PD effect evidence claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CLAIMS_PATH = Path("data/evidence/pd_effect_claims.json")

SOURCE_BY_DRUG = {
    "clarithromycin": "source_dailymed_clarithromycin_label",
    "fluconazole": "source_dailymed_fluconazole_label",
}

TARGET_PAIRS = {
    ("clarithromycin", "nausea"),
    ("fluconazole", "nausea"),
    ("clarithromycin", "QT_prolongation"),
    ("fluconazole", "QT_prolongation"),
}


def _load_claims() -> list[dict[str, Any]]:
    """Load PD effect evidence claims."""
    return json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))


def _write_claims(claims: list[dict[str, Any]]) -> None:
    """Write PD effect evidence claims."""
    CLAIMS_PATH.write_text(
        json.dumps(claims, indent=2) + "\n",
        encoding="utf-8",
    )


def _is_target_claim(claim: dict[str, Any]) -> bool:
    """Return whether the claim should receive a real source."""
    drug_id = claim["subject"]["id"]
    effect_id = claim["object"]["effect_id"]

    return (drug_id, effect_id) in TARGET_PAIRS


def _real_source_evidence(drug_id: str) -> dict[str, Any]:
    """Build a real source evidence item for a selected drug."""
    return {
        "source_id": SOURCE_BY_DRUG[drug_id],
        "evidence_type": "drug_label",
        "supports_claim": True,
        "confidence": "moderate",
        "notes": (
            "Selected real source record attached to demonstrate "
            "authoritative source support."
        ),
    }


def main() -> None:
    """Attach real source evidence to selected claims."""
    claims = _load_claims()
    updated_count = 0

    for claim in claims:
        if not _is_target_claim(claim):
            continue

        drug_id = claim["subject"]["id"]
        source_id = SOURCE_BY_DRUG[drug_id]

        existing_source_ids = {
            evidence["source_id"]
            for evidence in claim.get("evidence", [])
        }

        if source_id in existing_source_ids:
            continue

        claim.setdefault("evidence", []).append(
            _real_source_evidence(drug_id),
        )
        updated_count += 1

    _write_claims(claims)

    print(f"Updated {updated_count} selected PD effect claims.")


if __name__ == "__main__":
    main()