from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from data.loaders import load_drugs_curation
from tools.apply_strength_backfill import BACKFILL_PATH, apply, merge


def test_backfill_preserves_other_drug_edits_and_is_idempotent() -> None:
    payload = load_drugs_curation()
    for drug in payload["drugs"]:
        drug.pop("dosage_options", None)
    payload["drugs"][0]["notes"] = "User's local annotation"
    payload["drugs"].append(copy.deepcopy(payload["drugs"][0]))
    payload["drugs"][-1]["id"] = "user_local_drug"
    backfill = json.loads(BACKFILL_PATH.read_text(encoding="utf-8"))
    merged, count = merge(payload, backfill)
    assert count == 680
    assert merged["drugs"][0]["notes"] == "User's local annotation"
    assert merged["drugs"][-1]["id"] == "user_local_drug"
    assert merge(merged, backfill)[1] == 0


def test_conflicting_strength_blocks_merge_without_changing_input() -> None:
    payload = load_drugs_curation()
    option = next(d for d in payload["drugs"] if d["id"] == "ashwagandha")[
        "dosage_options"
    ][0]
    option["composition"] = "Different standardization"
    original = copy.deepcopy(payload)
    with pytest.raises(ValueError, match="conflicts"):
        merge(payload, json.loads(BACKFILL_PATH.read_text(encoding="utf-8")))
    assert payload == original


def test_backfill_source_file_covers_sourced_options() -> None:
    backfill = json.loads(Path(BACKFILL_PATH).read_text(encoding="utf-8"))
    assert len(backfill["options_by_drug"]) == 105
    assert sum(map(len, backfill["options_by_drug"].values())) == 680
    assert all(
        option["source_url"].startswith("https://")
        for rows in backfill["options_by_drug"].values()
        for option in rows
    )


def test_apply_writes_backup_and_keeps_user_notes(tmp_path: Path) -> None:
    path = tmp_path / "drugs.json"
    payload = load_drugs_curation()
    for drug in payload["drugs"]:
        drug.pop("dosage_options", None)
    payload["drugs"][0]["notes"] = "local edit retained"
    path.write_text(json.dumps(payload), encoding="utf-8")
    original = path.read_bytes()
    count, backup = apply(path, backup_dir=tmp_path / "backups")
    assert count == 680
    assert backup is not None and backup.read_bytes() == original
    assert json.loads(path.read_text(encoding="utf-8"))["drugs"][0]["notes"] == (
        "local edit retained"
    )
    assert apply(path, backup_dir=tmp_path / "backups") == (0, None)
