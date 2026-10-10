from __future__ import annotations

import copy
import json
from pathlib import Path

from data.curation.validate import validate_drugs_curation
from data.loaders import load_drugs_curation
from data.migrate_dosage_options import migrate
from data.seed_sqlite import apply_schema, connect, seed


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
        "must match an existing formulation" in error.message for error in errors
    )


def test_duplicate_dosage_option_is_rejected(tmp_path: Path) -> None:
    payload = _base_payload()
    payload["drugs"][0]["dosage_options"].append(
        copy.deepcopy(payload["drugs"][0]["dosage_options"][0])
    )
    errors = _validate(tmp_path, payload)
    assert any("Duplicate dosage option" in error.message for error in errors)


def test_sourced_strength_batch_is_formulation_matched(tmp_path: Path) -> None:
    payload = load_drugs_curation()
    options = [o for drug in payload["drugs"] for o in drug.get("dosage_options", [])]
    assert len(options) >= 752
    assert sum(bool(d.get("dosage_options")) for d in payload["drugs"]) >= 138
    assert all(option["source_url"].startswith("https://") for option in options)
    assert _validate(tmp_path, payload) == []
    ashwagandha = next(d for d in payload["drugs"] if d["id"] == "ashwagandha")
    assert "root extract" in ashwagandha["dosage_options"][0]["composition"]


def test_amoxicillin_and_amitriptyline_strengths_keep_labeled_forms() -> None:
    drugs = {d["id"]: d for d in load_drugs_curation()["drugs"]}
    amoxicillin = drugs["amoxicillin"]["dosage_options"]
    assert {
        (o["release_type"], o["dosage_form"], o["strength_value"], o["strength_unit"])
        for o in amoxicillin
    } == {
        ("ir", "capsule", 250, "mg"),
        ("ir", "capsule", 500, "mg"),
        ("ir", "tablet", 500, "mg"),
        ("ir", "tablet", 875, "mg"),
            ("ir", "chewable tablet", 125, "mg"),
            ("ir", "chewable tablet", 250, "mg"),
        *(
            ("ir", "oral suspension", value, "mg/5 mL")
            for value in (125, 200, 250, 400)
        ),
        ("er", "tablet", 775, "mg"),
    }
    assert all(
        o["source_url"].startswith("https://dailymed.nlm.nih.gov/")
        for o in amoxicillin
    )
    amitriptyline = drugs["amitriptyline"]["dosage_options"]
    assert {o["strength_value"] for o in amitriptyline} == {10, 25, 50, 75, 100, 150}
    assert all(
        o["dosage_form"] == "tablet" and o["release_type"] == "ir"
        for o in amitriptyline
    )


def test_strength_metadata_validation(tmp_path: Path) -> None:
    payload = _base_payload()
    option = payload["drugs"][0]["dosage_options"][0]
    option["source_url"] = "http://example.org"
    assert any("HTTPS" in e.message for e in _validate(tmp_path, payload))
    option["source_url"] = "https://example.org/label"
    option["composition"] = ""
    assert any("non-empty" in e.message for e in _validate(tmp_path, payload))
    option["composition"] = "root extract"
    option["strength_value"] = float("nan")
    assert any("strength_value" in e.path for e in _validate(tmp_path, payload))


def test_strength_migration_adds_metadata_to_existing_db(tmp_path: Path) -> None:
    expected_options = sum(
        len(drug.get("dosage_options", []))
        for drug in load_drugs_curation()["drugs"]
    )
    db = connect(tmp_path / "old.sqlite3")
    try:
        apply_schema(db)
        seed(db)
        db.execute("UPDATE drug SET notes='local note' WHERE id='vortioxetine'")
        db.execute("DROP TABLE drug_dosage_option")
        db.execute("""
            CREATE TABLE drug_dosage_option (
                drug_id TEXT NOT NULL,
                route TEXT NOT NULL,
                release_type TEXT NOT NULL,
                dosage_form TEXT NOT NULL,
                strength_value REAL NOT NULL,
                strength_unit TEXT NOT NULL,
                PRIMARY KEY(drug_id,route,release_type,dosage_form,
                            strength_value,strength_unit),
                FOREIGN KEY(drug_id) REFERENCES drug(id)
            )
        """)
        db.commit()
        assert migrate(db) == expected_options
        assert migrate(db) == expected_options
        assert (
            db.execute("SELECT count(*) FROM drug_dosage_option").fetchone()[0]
            == expected_options
        )
        row = db.execute(
            "SELECT source_url,composition FROM drug_dosage_option "
            "WHERE drug_id='ashwagandha'"
        ).fetchone()
        assert row["source_url"].startswith("https://pmc.ncbi.nlm.nih.gov/")
        assert "5% withanolides" in row["composition"]
        assert (
            db.execute("SELECT notes FROM drug WHERE id='vortioxetine'").fetchone()[0]
            == "local note"
        )
    finally:
        db.close()
