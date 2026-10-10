from __future__ import annotations

import copy
import json
from pathlib import Path

from data.curation.pk_observations import load_pk_curation
from data.curation.validate import validate_drugs_curation
from data.loaders import load_drugs_curation
from data.migrate_dosage_options import migrate
from data.seed_sqlite import apply_schema, connect, seed
from tools.apply_catalog_expansion import MANIFEST, PK_MANIFEST, merge_drugs, merge_pk


def test_expansion_covers_requested_items_and_references_specific_strengths(
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_id = {drug["id"]: drug for drug in manifest["drugs"]}
    assert len(by_id) == 49
    assert "tobacco_smoke" in by_id and "nicotine" not in by_id
    assert "psilocybin" in by_id and "psilocin" in by_id
    assert not by_id["synthetic_cannabinoids"]["enzymes"]
    assert not by_id["one_allyltheobromine"]["dosage_options"]
    assert {o["strength_value"] for o in by_id["dofetilide"]["dosage_options"]} == {
        125,
        250,
        500,
    }
    assert all(
        option["source_url"].startswith("https://")
        for drug in by_id.values()
        for option in drug["dosage_options"]
    )
    assert set(manifest["evidence_by_drug"]) == set(by_id)
    merged, count, conflicts = merge_drugs({"version": 1, "drugs": []}, manifest)
    assert count == 49
    assert not conflicts
    path = tmp_path / "drugs.json"
    path.write_text(json.dumps(merged), encoding="utf-8")
    assert not validate_drugs_curation(path)
    pk, obs_count = merge_pk(
        json.loads(PK_MANIFEST.read_text(encoding="utf-8")),
        json.loads(PK_MANIFEST.read_text(encoding="utf-8")),
    )
    assert obs_count == 0
    path.write_text(json.dumps(load_drugs_curation()), encoding="utf-8")
    pk_path = tmp_path / "pk.json"
    pk_path.write_text(
        Path("data/curation/pk_observations.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _, observations = load_pk_curation(pk_path, drugs_path=path)
    assert any(
        o.drug_id == "psilocybin" and o.analyte.startswith("psilocin")
        for o in observations
    )
    assert pk["observations"]


def test_local_fluvoxamine_is_enriched_without_overwriting_edits() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    custom = copy.deepcopy(
        next(d for d in manifest["drugs"] if d["id"] == "fluvoxamine")
    )
    custom["notes"] = "My locally curated fluvoxamine note"
    custom["dosage_options"] = custom["dosage_options"][:1]
    custom["enzymes"] = []
    result, added, conflicts = merge_drugs({"version": 1, "drugs": [custom]}, manifest)
    fluvoxamine = next(d for d in result["drugs"] if d["id"] == "fluvoxamine")
    assert added == 48
    assert fluvoxamine["notes"] == custom["notes"]
    assert len(fluvoxamine["dosage_options"]) == 5
    assert fluvoxamine["enzymes"]
    assert "fluvoxamine.notes: kept local value" in conflicts
    assert merge_drugs(result, manifest)[1] == 0


def test_expanded_dosage_options_preserve_product_specific_forms_and_units() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    drugs = {drug["id"]: drug for drug in manifest["drugs"]}
    assert sum(len(d["dosage_options"]) for d in drugs.values()) == 139

    def option(drug_id: str, form: str, value: float, unit: str) -> dict:
        matches = [
            entry
            for entry in drugs[drug_id]["dosage_options"]
            if entry["dosage_form"] == form
            and entry["strength_value"] == value
            and entry["strength_unit"] == unit
        ]
        assert len(matches) == 1, (drug_id, form, value, unit)
        return matches[0]

    assert option("metoprolol", "tablet", 200, "mg")["release_type"] == "er"
    assert option("metoprolol", "injection", 1, "mg/mL")["route"] == "iv"
    assert option("phenytoin", "chewable tablet", 50, "mg")["release_type"] == "ir"
    assert "free acid" in option("phenytoin", "chewable tablet", 50, "mg")[
        "product_name"
    ]
    assert option("phenytoin", "capsule", 100, "mg")["release_type"] == "er"
    assert option("linezolid", "oral suspension", 100, "mg/5 mL")["route"] == "oral"
    assert option("linezolid", "premixed infusion", 2, "mg/mL")["route"] == "iv"
    assert "opioid-tolerant" in option("morphine", "oral solution", 20, "mg/mL")[
        "product_name"
    ]
    assert option("rivaroxaban", "oral suspension", 1, "mg/mL")[
        "source_url"
    ].startswith("https://dailymed.nlm.nih.gov/")
    assert "0.3% hypericin" in option("st_johns_wort", "capsule", 300, "mg")[
        "composition"
    ]
    assert "root" in option("kava", "capsule", 250, "mg")["composition"]
    assert "not standardized" in option("ginseng", "capsule", 500, "mg")[
        "composition"
    ]
    assert not drugs["synthetic_cannabinoids"]["dosage_options"]


def test_new_strengths_merge_idempotently_into_an_existing_catalog(
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    merged, _, conflicts = merge_drugs(load_drugs_curation(), manifest)
    assert not conflicts
    assert sum(len(drug.get("dosage_options", [])) for drug in merged["drugs"]) == 819
    assert merge_drugs(merged, manifest) == (merged, 0, [])
    path = tmp_path / "drugs.json"
    path.write_text(json.dumps(merged), encoding="utf-8")
    assert not validate_drugs_curation(path)


def test_backfilled_liquid_and_release_options_reach_sqlite(
    tmp_path: Path, monkeypatch
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    merged, _, _ = merge_drugs(load_drugs_curation(), manifest)
    monkeypatch.setattr(
        "data.loaders.load_drugs_curation", lambda path=None: merged
    )
    monkeypatch.setattr(
        "data.curation.validate.assert_valid_drugs_curation", lambda: None
    )
    with connect(tmp_path / "expanded.sqlite3") as conn:
        apply_schema(conn)
        seed(conn)
        rows = conn.execute(
            "SELECT drug_id, route, release_type, dosage_form, strength_value, "
            "strength_unit FROM drug_dosage_option WHERE drug_id IN "
            "('linezolid', 'metoprolol', 'morphine')"
        ).fetchall()
    options = {tuple(row) for row in rows}
    assert ("linezolid", "oral", "ir", "oral suspension", 100, "mg/5 mL") in options
    assert ("linezolid", "iv", "ir", "premixed infusion", 2, "mg/mL") in options
    assert ("metoprolol", "oral", "er", "tablet", 200, "mg") in options
    assert ("morphine", "oral", "er", "tablet", 100, "mg") in options


def test_expanded_strength_migration_loads_every_option(
    tmp_path: Path, monkeypatch
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expanded, _, _ = merge_drugs(load_drugs_curation(), manifest)
    path = tmp_path / "drugs.json"
    path.write_text(json.dumps(expanded), encoding="utf-8")
    expected = sum(len(drug.get("dosage_options", [])) for drug in expanded["drugs"])
    monkeypatch.setattr("data.loaders.load_drugs_curation", lambda path=None: expanded)
    monkeypatch.setattr(
        "data.curation.validate.assert_valid_drugs_curation", lambda: None
    )
    with connect(tmp_path / "expanded.sqlite3") as conn:
        apply_schema(conn)
        seed(conn)
        conn.execute("DELETE FROM drug_dosage_option")
        assert migrate(conn, curation_path=path) == expected
        assert migrate(conn, curation_path=path) == expected
        assert (
            conn.execute("SELECT count(*) FROM drug_dosage_option").fetchone()[0]
            == expected
        )
