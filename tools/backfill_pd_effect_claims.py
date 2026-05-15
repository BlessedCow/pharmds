"""Backfill internal curated evidence claims for ontology PD effects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DRUGS_PATH = Path("data/curation/drugs.json")
CLAIMS_PATH = Path("data/evidence/pd_effect_claims.json")

SOURCE_ID = "source_internal_curated_pd_effects_v1"
CLAIM_TYPE = "pd_effect"
PREDICATE = "has_pd_effect"


def _load_json(path: Path) -> Any:
    """Load JSON from a path."""
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    """Write formatted JSON to a path."""
    path.write_text(
        json.dumps(data, indent=2) + "\n",
        encoding="utf-8",
    )


def _claim_id(drug_id: str, effect_id: str) -> str:
    """Return the canonical claim ID for a drug PD effect."""
    return f"claim_{drug_id}_pd_effect_{effect_id}_001"


def _build_claim(drug_id: str, effect_id: str) -> dict[str, Any]:
    """Build one approved internal curated PD effect claim."""
    return {
        "claim_id": _claim_id(drug_id, effect_id),
        "claim_type": CLAIM_TYPE,
        "subject": {
            "entity_type": "drug",
            "id": drug_id,
        },
        "predicate": PREDICATE,
        "object": {
            "effect_id": effect_id,
        },
        "evidence": [
            {
                "source_id": SOURCE_ID,
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": (
                    "Initial curated PD effect claim migrated from the "
                    "existing drug ontology."
                ),
            }
        ],
        "review": {
            "status": "approved",
            "reviewed_by": "maintainer",
            "reviewed_at": None,
        },
        "claim_status": "active",
    }


def _iter_drug_pd_effects() -> list[tuple[str, str]]:
    """Return all unique drug PD effect pairs from the curated ontology."""
    raw = _load_json(DRUGS_PATH)
    pairs: set[tuple[str, str]] = set()

    for drug in raw["drugs"]:
        drug_id = drug["id"]

        for pd_effect in drug.get("pd_effects", []) or []:
            effect_id = pd_effect["effect_id"]
            pairs.add((drug_id, effect_id))

    return sorted(pairs)


def main() -> None:
    """Append missing PD effect evidence claims."""
    claims = _load_json(CLAIMS_PATH)
    existing_claim_ids = {
        claim["claim_id"]
        for claim in claims
    }

    new_claims = []

    for drug_id, effect_id in _iter_drug_pd_effects():
        claim_id = _claim_id(drug_id, effect_id)

        if claim_id in existing_claim_ids:
            continue

        new_claims.append(_build_claim(drug_id, effect_id))

    claims.extend(new_claims)
    claims.sort(key=lambda claim: claim["claim_id"])

    _write_json(CLAIMS_PATH, claims)

    print(f"Added {len(new_claims)} PD effect evidence claims.")
    print(f"Total PD effect evidence claims: {len(claims)}")


if __name__ == "__main__":
    main()