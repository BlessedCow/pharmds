from __future__ import annotations

import copy
import json
from pathlib import Path

from data.curation.validate import validate_drugs_curation


def _base_payload() -> dict:
    return {
        "version": 1,
        "drugs": [
            {
                "id": "example",
                "generic_name": "example",
                "drug_class": "test",
                "therapeutic_index": "wide",
                "aliases": [],
                "release_types": ["ir"],
                "notes": "test",
                "enzymes": [],
                "transporters": [],
                "pd_effects": [],
                "parameters": {
                    "prodrug": False,
                    "active_metabolite": False,
                    "renal_clearance_flag": False,
                    "half_life_bucket": "medium",
                },
                "formulations": [{"route": "oral", "release_types": ["ir"]}],
                "dosage_options": [
                    {
                        "route": "oral",
                        "release_type": "ir",
                        "dosage_form": "tablet",
                        "strength_value": 10,
                        "strength_unit": "mg",
                    }
                ],
            }
        ],
    }


def _validate(tmp_path: Path, payload: dict):
    path = tmp_path / "drugs.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return validate_drugs_curation(path)


def test_valid_dosage_option_passes(tmp_path: Path) -> None:
    assert _validate(tmp_path, _base_payload()) == []


def test_dosage_must_match_curated_formulation(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["drugs"][0]["dosage_options"][0]["release_type"] = "er"
    errors = _validate(tmp_path, payload)
    assert any(
        "must match an existing formulation" in error.message
        for error in errors
    )


def test_duplicate_dosage_option_is_rejected(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["drugs"][0]["dosage_options"].append(
        copy.deepcopy(payload["drugs"][0]["dosage_options"][0])
    )
    errors = _validate(tmp_path, payload)
    assert any("Duplicate dosage option" in error.message for error in errors)
