from __future__ import annotations

from typing import Any

from core.evidence.conflicts import (
    claim_has_supporting_evidence,
    classify_evidence_support,
    count_evidence_support,
)
from core.evidence.loader import (
    get_approved_active_pd_effect_claims_for_drug,
    get_approved_active_pd_effect_claims_for_drug_effect,
    get_source_by_id,
)


def build_source_trace(source_id: str) -> dict[str, Any]:
    source = get_source_by_id(source_id)

    if source is None:
        return {
            "source_id": source_id,
            "found": False,
            "title": None,
            "source_type": None,
            "publisher": None,
            "url": None,
            "published_at": None,
            "accessed_at": None,
            "version": None,
            "reliability_tier": None,
        }

    return {
        "source_id": source["source_id"],
        "found": True,
        "title": source["title"],
        "source_type": source["source_type"],
        "publisher": source["publisher"],
        "url": source["url"],
        "published_at": source.get("published_at"),
        "accessed_at": source.get("accessed_at"),
        "version": source.get("version"),
        "reliability_tier": source["reliability_tier"],
    }


def build_pd_effect_claim_trace(claim: dict[str, Any]) -> dict[str, Any]:
    evidence_items = []

    for evidence in claim.get("evidence", []):
        source_trace = build_source_trace(evidence["source_id"])

        evidence_items.append(
            {
                "source": source_trace,
                "evidence_type": evidence["evidence_type"],
                "supports_claim": evidence["supports_claim"],
                "confidence": evidence["confidence"],
                "notes": evidence["notes"],
            }
        )

    evidence_support_counts = count_evidence_support(evidence_items)

    return {
        "claim_id": claim["claim_id"],
        "claim_type": claim["claim_type"],
        "drug_id": claim["subject"]["id"],
        "predicate": claim["predicate"],
        "effect_id": claim["object"]["effect_id"],
        "claim_status": claim["claim_status"],
        "review": claim["review"],
        "contributor": claim.get("contributor"),
        "evidence_support_status": classify_evidence_support(evidence_items),
        "evidence_support_counts": evidence_support_counts,
        "evidence": evidence_items,
    }


def build_pd_effect_traces_for_drug_effect(
    drug_id: str,
    effect_id: str,
) -> list[dict[str, Any]]:
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        drug_id,
        effect_id,
    )

    return [build_pd_effect_claim_trace(claim) for claim in claims]


def build_pd_effect_traces_for_drug(
    drug_id: str,
) -> list[dict[str, Any]]:
    claims = get_approved_active_pd_effect_claims_for_drug(drug_id)

    return [build_pd_effect_claim_trace(claim) for claim in claims]


def has_approved_active_pd_effect_evidence(
    drug_id: str,
    effect_id: str,
) -> bool:
    claims = get_approved_active_pd_effect_claims_for_drug_effect(
        drug_id,
        effect_id,
    )

    return any(claim_has_supporting_evidence(claim) for claim in claims)