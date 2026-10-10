from __future__ import annotations

import copy
import hashlib
import json
import sqlite3

from data.loaders import load_drugs_curation
from data.migrate_drug_notes import migrate
from tools.apply_catalog_note_backfill import MANIFEST_PATH, merge


def test_catalog_notes_have_a_source_and_similar_depth() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    catalog = load_drugs_curation()
    assert set(manifest["entries"]) == {d["id"] for d in catalog["drugs"]}
    for entry in manifest["entries"].values():
        assert 40 <= len(entry["notes"].split()) <= 85
        assert entry["note_sources"]
        assert all(source.startswith("https://") for source in entry["note_sources"])


def test_note_merge_preserves_custom_notes_and_added_medications() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    reference = load_drugs_curation()
    target = copy.deepcopy(reference)
    first = target["drugs"][0]
    second = target["drugs"][1]
    first["notes"] = "A locally edited note."
    first.pop("brand_names", None)
    second["notes"] = "Local author's original note."
    second.pop("brand_names", None)
    added = copy.deepcopy(first)
    added["id"] = "custom_addition"
    added["notes"] = "Keep this entire drug."
    target["drugs"].append(added)
    updated, notes, brands, skipped = merge(target, manifest)
    assert notes == 0
    assert brands == 2
    assert len(skipped) == 2
    assert updated["drugs"][-1] == added
    assert updated["drugs"][0]["notes"] == first["notes"]
    assert updated["drugs"][1]["notes"] == second["notes"]
    assert merge(updated, manifest)[1:3] == (0, 0)


def test_note_merge_updates_only_matching_baseline() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    catalog = load_drugs_curation()
    drug = catalog["drugs"][0]
    original = "Earlier short catalog note."
    drug["notes"] = original
    manifest["entries"][drug["id"]]["baseline_notes_sha256"] = hashlib.sha256(
        original.encode()
    ).hexdigest()
    updated, notes, brands, skipped = merge(catalog, manifest)
    assert (notes, brands, skipped) == (1, 0, [])
    assert updated["drugs"][0]["notes"] == manifest["entries"][drug["id"]]["notes"]


def test_notes_migration_only_updates_changed_existing_rows(tmp_path) -> None:
    payload = load_drugs_curation()
    selected = payload["drugs"][0]
    path = tmp_path / "drugs.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE drug (id TEXT PRIMARY KEY, notes TEXT)")
    conn.executemany(
        "INSERT INTO drug (id, notes) VALUES (?, ?)",
        [(selected["id"], "old note"), ("custom", "own note")],
    )
    assert migrate(conn, curation_path=path) == 1
    assert migrate(conn, curation_path=path) == 0
    assert (
        conn.execute("SELECT notes FROM drug WHERE id='custom'").fetchone()[0]
        == "own note"
    )
    assert (
        conn.execute("SELECT notes FROM drug WHERE id=?", (selected["id"],)).fetchone()[
            0
        ]
        == selected["notes"]
    )
