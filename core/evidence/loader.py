from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SOURCES_PATH = ROOT / "data" / "evidence" / "sources.json"
PD_EFFECT_CLAIMS_PATH = ROOT / "data" / "evidence" / "pd_effect_claims.json"
PD_EFFECT_CLAIMS_DIR = ROOT / "data" / "evidence" / "pd_effect_claims"

SOURCE_REQUIRED_FIELDS = {
    "source_id",
    "title",
    "source_type",
    "publisher",
    "url",
    "published_at",
    "accessed_at",
    "version",
    "reliability_tier",
}
SOURCE_ALLOWED_TYPES = {
    "drug_label",
    "clinical_guideline",
    "review_article",
    "primary_literature",
    "case_report",
    "mechanistic_inference",
    "internal_curated_entry",
}
SOURCE_ALLOWED_RELIABILITY_TIERS = {
    "authoritative",
    "high",
    "moderate",
    "low",
    "curated",
}


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    data = _load_json(path)

    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {path}")

    return data


def _load_segmented_pd_effect_claims() -> list[dict[str, Any]]:
    if not PD_EFFECT_CLAIMS_DIR.exists():
        return []

    claims: list[dict[str, Any]] = []

    for path in sorted(PD_EFFECT_CLAIMS_DIR.rglob("*.json")):
        claims.extend(_load_json_list(path))

    return claims


def _require_text_field(
    item: dict[str, Any],
    *,
    field: str,
    item_label: str,
) -> str:
    value = item.get(field)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{item_label} must include non-empty {field!r}")

    return value


def validate_source_records(
    sources: list[dict[str, Any]],
) -> None:
    """Validate source registry structure and source ID uniqueness."""
    seen_source_ids: set[str] = set()

    for index, source in enumerate(sources):
        item_label = f"source record at index {index}"

        if not isinstance(source, dict):
            raise ValueError(f"{item_label} must be an object")

        missing_fields = sorted(SOURCE_REQUIRED_FIELDS - source.keys())
        if missing_fields:
            raise ValueError(
                f"{item_label} is missing required fields: "
                f"{', '.join(missing_fields)}"
            )

        source_id = _require_text_field(
            source,
            field="source_id",
            item_label=item_label,
        )
        _require_text_field(source, field="title", item_label=source_id)
        source_type = _require_text_field(
            source,
            field="source_type",
            item_label=source_id,
        )
        _require_text_field(source, field="publisher", item_label=source_id)
        reliability_tier = _require_text_field(
            source,
            field="reliability_tier",
            item_label=source_id,
        )

        if source_id in seen_source_ids:
            raise ValueError(f"Duplicate evidence source_id: {source_id}")
        seen_source_ids.add(source_id)

        if source_type not in SOURCE_ALLOWED_TYPES:
            raise ValueError(
                f"{source_id} has unknown source_type: {source_type}"
            )

        if reliability_tier not in SOURCE_ALLOWED_RELIABILITY_TIERS:
            raise ValueError(
                f"{source_id} has unknown reliability_tier: "
                f"{reliability_tier}"
            )

def build_source_index(
    sources: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build a source_id keyed lookup after validating source records."""
    validate_source_records(sources)

    return {source["source_id"]: source for source in sources}

def validate_claim_source_references(
    claims: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> None:
    """Validate that every claim evidence source_id exists."""
    known_source_ids = {source["source_id"] for source in sources}

    for claim in claims:
        claim_id = claim.get("claim_id", "unknown_claim")

        for evidence in claim.get("evidence", []) or []:
            if not isinstance(evidence, dict):
                continue

            source_id = evidence.get("source_id")
            if source_id in known_source_ids:
                continue

            raise ValueError(
                f"Evidence claim {claim_id} references unknown source_id: "
                f"{source_id}"
            )


def validate_evidence_source_registry() -> None:
    """Validate source records and claim source references."""
    sources = load_sources()
    claims = load_pd_effect_claims()

    validate_source_records(sources)
    validate_claim_source_references(claims, sources)

@lru_cache(maxsize=1)
def load_sources() -> list[dict[str, Any]]:
    sources = _load_json_list(SOURCES_PATH)
    validate_source_records(sources)

    return sources

@lru_cache(maxsize=1)
def load_source_index() -> dict[str, dict[str, Any]]:
    return build_source_index(load_sources())

@lru_cache(maxsize=1)
def load_pd_effect_claims() -> list[dict[str, Any]]:
    claims = _load_json_list(PD_EFFECT_CLAIMS_PATH)
    claims.extend(_load_segmented_pd_effect_claims())
    validate_claim_source_references(claims, load_sources())

    return claims


def get_source_by_id(source_id: str) -> dict[str, Any] | None:
    return load_source_index().get(source_id)


def get_pd_effect_claims_for_drug(drug_id: str) -> list[dict[str, Any]]:
    return [
        claim
        for claim in load_pd_effect_claims()
        if claim.get("claim_type") == "pd_effect"
        and claim.get("subject", {}).get("entity_type") == "drug"
        and claim.get("subject", {}).get("id") == drug_id
    ]


def get_pd_effect_claims_for_effect(effect_id: str) -> list[dict[str, Any]]:
    return [
        claim
        for claim in load_pd_effect_claims()
        if claim.get("claim_type") == "pd_effect"
        and claim.get("object", {}).get("effect_id") == effect_id
    ]


def get_pd_effect_claims_for_drug_effect(
    drug_id: str,
    effect_id: str,
) -> list[dict[str, Any]]:
    return [
        claim
        for claim in load_pd_effect_claims()
        if claim.get("claim_type") == "pd_effect"
        and claim.get("subject", {}).get("entity_type") == "drug"
        and claim.get("subject", {}).get("id") == drug_id
        and claim.get("object", {}).get("effect_id") == effect_id
    ]


def get_approved_active_pd_effect_claims() -> list[dict[str, Any]]:
    return [
        claim
        for claim in load_pd_effect_claims()
        if claim.get("claim_type") == "pd_effect"
        and claim.get("claim_status") == "active"
        and claim.get("review", {}).get("status") == "approved"
    ]


def get_approved_active_pd_effect_claims_for_drug(
    drug_id: str,
) -> list[dict[str, Any]]:
    return [
        claim
        for claim in get_approved_active_pd_effect_claims()
        if claim.get("subject", {}).get("entity_type") == "drug"
        and claim.get("subject", {}).get("id") == drug_id
    ]


def get_approved_active_pd_effect_claims_for_drug_effect(
    drug_id: str,
    effect_id: str,
) -> list[dict[str, Any]]:
    return [
        claim
        for claim in get_approved_active_pd_effect_claims()
        if claim.get("subject", {}).get("entity_type") == "drug"
        and claim.get("subject", {}).get("id") == drug_id
        and claim.get("object", {}).get("effect_id") == effect_id
    ]