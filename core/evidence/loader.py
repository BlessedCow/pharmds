from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SOURCES_PATH = ROOT / "data" / "evidence" / "sources.json"
PD_EFFECT_CLAIMS_PATH = ROOT / "data" / "evidence" / "pd_effect_claims.json"


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_sources() -> list[dict[str, Any]]:
    return _load_json(SOURCES_PATH)


@lru_cache(maxsize=1)
def load_pd_effect_claims() -> list[dict[str, Any]]:
    return _load_json(PD_EFFECT_CLAIMS_PATH)


def get_source_by_id(source_id: str) -> dict[str, Any] | None:
    for source in load_sources():
        if source.get("source_id") == source_id:
            return source

    return None


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