"""Report curated ontology facts that are missing evidence claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DRUGS_PATH = PROJECT_ROOT / "data" / "curation" / "drugs.json"
PD_EFFECT_CLAIMS_PATH = (
    PROJECT_ROOT / "data" / "evidence" / "pd_effect_claims.json"
)


def load_json(path: Path) -> Any:
    """Load JSON from a file path."""
    return json.loads(path.read_text(encoding="utf-8"))


def curated_pd_effect_pairs() -> set[tuple[str, str]]:
    """Return all curated drug/effect pairs from the ontology."""
    raw = load_json(DRUGS_PATH)

    pairs = set()

    for drug in raw["drugs"]:
        drug_id = drug["id"]

        for pd_effect in drug.get("pd_effects", []) or []:
            pairs.add((drug_id, pd_effect["effect_id"]))

    return pairs


def approved_active_pd_effect_claim_pairs() -> set[tuple[str, str]]:
    """Return drug/effect pairs with approved active PD evidence claims."""
    claims = load_json(PD_EFFECT_CLAIMS_PATH)

    pairs = set()

    for claim in claims:
        if claim.get("claim_type") != "pd_effect":
            continue

        if claim.get("claim_status") != "active":
            continue

        review = claim.get("review", {})

        if review.get("status") != "approved":
            continue

        drug_id = claim["subject"]["id"]
        effect_id = claim["object"]["effect_id"]

        pairs.add((drug_id, effect_id))

    return pairs


def missing_pd_effect_claim_pairs() -> list[tuple[str, str]]:
    """Return curated PD effect pairs missing approved active evidence claims."""
    missing = (
        curated_pd_effect_pairs()
        - approved_active_pd_effect_claim_pairs()
    )

    return sorted(missing)


def build_report_lines() -> list[str]:
    """Return a human-readable evidence gap report."""
    missing_pairs = missing_pd_effect_claim_pairs()

    lines = [
        "Evidence gap report",
        "",
        "PD effects without approved active evidence claims:",
    ]

    if not missing_pairs:
        lines.append("- None")
        return lines

    for drug_id, effect_id in missing_pairs:
        lines.append(f"- {drug_id} -> {effect_id}")

    return lines


def main() -> None:
    """Print the evidence gap report."""
    for line in build_report_lines():
        print(line)


if __name__ == "__main__":
    main()