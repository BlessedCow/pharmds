"""Evidence source quality reporting helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _source_id(source: dict[str, Any]) -> str | None:
    value = source.get("source_id")

    if isinstance(value, str) and value:
        return value

    return None


def _claim_source_ids(claim: dict[str, Any]) -> set[str]:
    source_ids = set()

    for evidence in claim.get("evidence", []) or []:
        if not isinstance(evidence, dict):
            continue

        source_id = evidence.get("source_id")
        if isinstance(source_id, str) and source_id:
            source_ids.add(source_id)

    return source_ids


def collect_claim_source_ids(
    claims: list[dict[str, Any]],
) -> set[str]:
    """Return all source IDs referenced by evidence claims."""
    source_ids = set()

    for claim in claims:
        source_ids.update(_claim_source_ids(claim))

    return source_ids


def find_claims_with_missing_sources(
    claims: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return claim/source references where the source record is missing."""
    known_source_ids = {
        source_id
        for source in sources
        if (source_id := _source_id(source))
    }
    missing = []

    for claim in claims:
        claim_id = claim.get("claim_id", "unknown_claim")

        for source_id in sorted(_claim_source_ids(claim)):
            if source_id in known_source_ids:
                continue

            missing.append(
                {
                    "claim_id": claim_id,
                    "source_id": source_id,
                }
            )

    return missing


def find_unused_sources(
    claims: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return source records that are not referenced by any claim."""
    referenced_source_ids = collect_claim_source_ids(claims)
    unused = []

    for source in sources:
        source_id = _source_id(source)

        if source_id is None:
            continue

        if source_id not in referenced_source_ids:
            unused.append(source)

    return unused


def _missing_fields_for_source(source: dict[str, Any]) -> list[str]:
    missing = []

    for field in [
        "source_id",
        "title",
        "source_type",
        "publisher",
        "reliability_tier",
    ]:
        if source.get(field) in (None, ""):
            missing.append(field)

    if source.get("url") in (None, ""):
        missing.append("url")

    if source.get("published_at") in (None, ""):
        missing.append("published_at")

    if source.get("accessed_at") in (None, ""):
        missing.append("accessed_at")

    return missing


def find_sources_with_missing_metadata(
    sources: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return sources with missing recommended metadata fields."""
    items = []

    for source in sources:
        missing_fields = _missing_fields_for_source(source)

        if not missing_fields:
            continue

        items.append(
            {
                "source_id": source.get("source_id", "unknown_source"),
                "missing_fields": missing_fields,
            }
        )

    return items


def build_evidence_source_quality_report(
    claims: list[dict[str, Any]],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a maintainer-facing source quality report."""
    source_type_counts = Counter()
    reliability_tier_counts = Counter()

    for source in sources:
        source_type = source.get("source_type", "unknown")
        reliability_tier = source.get("reliability_tier", "unknown")

        source_type_counts[source_type] += 1
        reliability_tier_counts[reliability_tier] += 1

    referenced_source_ids = collect_claim_source_ids(claims)
    unused_sources = find_unused_sources(claims, sources)
    missing_source_references = find_claims_with_missing_sources(
        claims,
        sources,
    )
    sources_missing_metadata = find_sources_with_missing_metadata(sources)

    return {
        "report_type": "evidence_source_quality_report",
        "total_sources": len(sources),
        "total_claims": len(claims),
        "referenced_source_count": len(referenced_source_ids),
        "unused_source_count": len(unused_sources),
        "missing_source_reference_count": len(missing_source_references),
        "sources_missing_metadata_count": len(sources_missing_metadata),
        "source_type_counts": dict(sorted(source_type_counts.items())),
        "reliability_tier_counts": dict(
            sorted(reliability_tier_counts.items())
        ),
        "unused_sources": unused_sources,
        "missing_source_references": missing_source_references,
        "sources_missing_metadata": sources_missing_metadata,
    }