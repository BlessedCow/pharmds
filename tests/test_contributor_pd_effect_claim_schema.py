import json
from pathlib import Path

from jsonschema import Draft202012Validator

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    PROJECT_ROOT
    / "data"
    / "evidence"
    / "schemas"
    / "contributor_pd_effect_claim.schema.json"
)


def _load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _valid_submission():
    return {
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "fluconazole",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "QT_prolongation",
        },
        "evidence": [
            {
                "source_id": "source_dailymed_fluconazole_label",
                "evidence_type": "drug_label",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Contributor-submitted label evidence.",
            }
        ],
        "review": {
            "status": "submitted",
        },
    }


def _validation_errors(payload):
    schema = _load_schema()
    validator = Draft202012Validator(schema)

    return sorted(
        validator.iter_errors(payload),
        key=lambda error: list(error.path),
    )


def test_valid_contributor_pd_effect_claim_submission_matches_schema():
    assert _validation_errors(_valid_submission()) == []


def test_contributor_pd_effect_claim_submission_requires_submitted_review_status():
    payload = _valid_submission()
    payload["review"]["status"] = "approved"

    errors = _validation_errors(payload)

    assert errors
    assert list(errors[0].path) == ["review", "status"]


def test_contributor_pd_effect_claim_submission_rejects_extra_fields():
    payload = _valid_submission()
    payload["claim_status"] = "active"

    errors = _validation_errors(payload)

    assert errors
    assert list(errors[0].path) == []

def test_contributor_pd_effect_claim_submission_requires_evidence():
    payload = _valid_submission()
    payload["evidence"] = []

    errors = _validation_errors(payload)

    assert errors
    assert list(errors[0].path) == ["evidence"]