"""Append the next batch of internal PD evidence claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CLAIMS_PATH = Path("data/evidence/pd_effect_claims.json")

CLAIM_SPECS = [
    ("vortioxetine", "insomnia_risk"),
    ("varenicline", "insomnia_risk"),
    ("vortioxetine", "activation_agitation_risk"),
    ("varenicline", "activation_agitation_risk"),
    ("hydroxyzine", "anticholinergic_effects"),
    ("paroxetine", "anticholinergic_effects"),
    ("trazodone", "orthostatic_hypotension"),
    ("clonidine", "orthostatic_hypotension"),
]


def build_claim(drug_id: str, effect_id: str) -> dict[str, Any]:
    """Build one internal curated PD effect evidence claim."""
    return {
        "claim_id": f"claim_{drug_id}_pd_effect_{effect_id}_001",
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": drug_id,
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": effect_id,
        },
        "evidence": [
            {
                "source_id": "source_internal_curated_pd_effects_v1",
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


def main() -> None:
    """Append missing claims without duplicating existing claim IDs."""
    claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))

    existing_claim_ids = {
        claim["claim_id"]
        for claim in claims
    }

    new_claims = [
        build_claim(drug_id, effect_id)
        for drug_id, effect_id in CLAIM_SPECS
        if build_claim(drug_id, effect_id)["claim_id"]
        not in existing_claim_ids
    ]

    claims.extend(new_claims)

    CLAIMS_PATH.write_text(
        json.dumps(claims, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Added {len(new_claims)} PD evidence claims.")


if __name__ == "__main__":
    main()