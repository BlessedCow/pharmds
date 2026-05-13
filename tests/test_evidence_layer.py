from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

SOURCES_PATH = ROOT / "data" / "evidence" / "sources.json"
PD_EFFECT_CLAIMS_PATH = ROOT / "data" / "evidence" / "pd_effect_claims.json"

SOURCE_SCHEMA_PATH = (
    ROOT / "schemas" / "evidence" / "evidence_source.schema.json"
)
CLAIM_SCHEMA_PATH = (
    ROOT / "schemas" / "evidence" / "evidence_claim.schema.json"
)


def _load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _load_sources():
    return _load_json(SOURCES_PATH)


def _load_pd_effect_claims():
    return _load_json(PD_EFFECT_CLAIMS_PATH)


def _load_source_schema():
    return _load_json(SOURCE_SCHEMA_PATH)


def _load_claim_schema():
    return _load_json(CLAIM_SCHEMA_PATH)


def _load_drugs():
    candidate_paths = [
        ROOT / "curation" / "drugs.json",
        ROOT / "data" / "curation" / "drugs.json",
        ROOT / "data" / "drugs.json",
        ROOT / "drugs.json",
    ]

    path = next((path for path in candidate_paths if path.exists()), None)

    if path is None:
        searched = "\n".join(str(candidate) for candidate in candidate_paths)
        raise FileNotFoundError(
            "Could not find drugs.json. Searched:\n" + searched
        )

    data = _load_json(path)

    if isinstance(data, list):
        return {
            drug["id"]: drug
            for drug in data
            if isinstance(drug, dict) and drug.get("id")
        }

    if isinstance(data, dict):
        if "drugs" in data and isinstance(data["drugs"], list):
            return {
                drug["id"]: drug
                for drug in data["drugs"]
                if isinstance(drug, dict) and drug.get("id")
            }

        return {
            drug_id: drug
            for drug_id, drug in data.items()
            if isinstance(drug, dict)
        }

    return {}

def _pd_effect_id(effect):
    if isinstance(effect, str):
        return effect

    if isinstance(effect, dict):
        for key in ("id", "effect_id", "effect", "name"):
            value = effect.get(key)
            if isinstance(value, str):
                return value

    return None

def _collect_known_pd_effects(drugs: dict):
    effects = set()

    for drug in drugs.values():
        for effect in drug.get("pd_effects", []):
            effect_id = _pd_effect_id(effect)

            if effect_id:
                effects.add(effect_id)

    return effects


def test_evidence_sources_match_schema():
    schema = _load_source_schema()
    validator = Draft202012Validator(schema)

    for source in _load_sources():
        errors = sorted(validator.iter_errors(source), key=lambda e: e.path)
        assert not errors, [
            f"{list(error.path)}: {error.message}" for error in errors
        ]


def test_pd_effect_claims_match_schema():
    schema = _load_claim_schema()
    validator = Draft202012Validator(schema)

    for claim in _load_pd_effect_claims():
        errors = sorted(validator.iter_errors(claim), key=lambda e: e.path)
        assert not errors, [
            f"{list(error.path)}: {error.message}" for error in errors
        ]


def test_evidence_source_ids_are_unique():
    sources = _load_sources()
    source_ids = [source["source_id"] for source in sources]

    assert len(source_ids) == len(set(source_ids))


def test_pd_effect_claim_ids_are_unique():
    claims = _load_pd_effect_claims()
    claim_ids = [claim["claim_id"] for claim in claims]

    assert len(claim_ids) == len(set(claim_ids))


def test_pd_effect_claim_sources_exist():
    sources = _load_sources()
    known_source_ids = {source["source_id"] for source in sources}

    for claim in _load_pd_effect_claims():
        for evidence in claim["evidence"]:
            assert evidence["source_id"] in known_source_ids, claim["claim_id"]


def test_pd_effect_claim_subject_drugs_exist():
    drugs = _load_drugs()
    known_drug_ids = set(drugs)

    for claim in _load_pd_effect_claims():
        drug_id = claim["subject"]["id"]
        assert drug_id in known_drug_ids, claim["claim_id"]


def test_pd_effect_claim_objects_exist_in_current_ontology():
    drugs = _load_drugs()
    known_pd_effects = _collect_known_pd_effects(drugs)

    for claim in _load_pd_effect_claims():
        effect_id = claim["object"]["effect_id"]
        assert effect_id in known_pd_effects, claim["claim_id"]


def test_approved_active_pd_effect_claims_match_drug_json():
    drugs = _load_drugs()

    for claim in _load_pd_effect_claims():
        if claim["review"]["status"] != "approved":
            continue

        if claim["claim_status"] != "active":
            continue

        drug_id = claim["subject"]["id"]
        effect_id = claim["object"]["effect_id"]

        drug = drugs[drug_id]
        drug_pd_effects = {
            pd_effect_id
            for pd_effect_id in (
                _pd_effect_id(effect) for effect in drug.get("pd_effects", [])
            )
            if pd_effect_id
        }

        assert effect_id in drug_pd_effects, claim["claim_id"]


def test_no_duplicate_pd_effect_claims_for_same_drug_effect_source():
    seen = set()

    for claim in _load_pd_effect_claims():
        drug_id = claim["subject"]["id"]
        effect_id = claim["object"]["effect_id"]

        for evidence in claim["evidence"]:
            key = (
                drug_id,
                effect_id,
                evidence["source_id"],
            )

            assert key not in seen, claim["claim_id"]
            seen.add(key)