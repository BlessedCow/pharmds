"""Merge reviewed catalog notes and brand display names into local curation."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from data.curation.validate import validate_drugs_curation
from data.loaders import load_drugs_curation
from tools.curation_gui import atomic_save_payload

MANIFEST_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "curation"
    / "catalog_note_backfill.json"
)


def merge(payload: dict, manifest: dict) -> tuple[dict, int, int, list[str]]:
    if manifest.get("version") != 1 or not isinstance(manifest.get("entries"), dict):
        raise ValueError("Invalid catalog note backfill")
    result = copy.deepcopy(payload)
    by_id = {drug["id"]: drug for drug in result["drugs"]}
    notes_changed = 0
    brands_changed = 0
    skipped: list[str] = []
    for drug_id, item in manifest["entries"].items():
        drug = by_id.get(drug_id)
        if drug is None:
            skipped.append(f"{drug_id} (not in local catalog)")
            continue
        current = drug.get("notes", "")
        expected = item["baseline_notes_sha256"]
        if current != item["notes"]:
            if hashlib.sha256(current.encode("utf-8")).hexdigest() == expected:
                drug["notes"] = item["notes"]
                notes_changed += 1
            else:
                skipped.append(f"{drug_id} (locally edited notes)")
        if "brand_names" not in drug:
            drug["brand_names"] = copy.deepcopy(item["brand_names"])
            brands_changed += 1
    return result, notes_changed, brands_changed, skipped


def apply(
    path: Path,
    manifest_path: Path = MANIFEST_PATH,
    *,
    backup_dir: Path | None = None,
) -> tuple[int, int, list[str], Path | None]:
    payload = load_drugs_curation(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    updated, notes, brands, skipped = merge(payload, manifest)
    if not notes and not brands:
        return notes, brands, skipped, None
    if validate_drugs_curation(path):
        raise ValueError("Local drug curation is invalid before merge")
    backup = atomic_save_payload(
        updated, path=path, **({"backup_dir": backup_dir} if backup_dir else {})
    )
    return notes, brands, skipped, backup


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--drugs",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "data"
        / "curation"
        / "drugs.json",
    )
    args = parser.parse_args()
    notes, brands, skipped, backup = apply(args.drugs)
    print(f"Updated {notes} notes and {brands} brand-name lists in {args.drugs}.")
    if skipped:
        print("Preserved/skipped: " + ", ".join(skipped))
    if backup:
        print(f"Previous file: {backup}")


if __name__ == "__main__":
    main()
