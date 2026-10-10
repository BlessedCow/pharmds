"""Merge the sourced strength batch into local drug curation without losing edits."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

from data.curation.validate import validate_drugs_curation
from data.loaders import load_drugs_curation
from tools.curation_gui import atomic_save_payload

BACKFILL_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "curation" / "strength_backfill.json"
)


def option_key(option: dict) -> tuple[str, str, str, float, str]:
    return (
        option["route"],
        option["release_type"],
        option["dosage_form"].casefold(),
        float(option["strength_value"]),
        option["strength_unit"].casefold(),
    )


def merge(payload: dict, backfill: dict) -> tuple[dict, int]:
    if backfill.get("version") != 1 or not isinstance(
        backfill.get("options_by_drug"), dict
    ):
        raise ValueError("Invalid sourced strength backfill")
    result = copy.deepcopy(payload)
    by_id = {drug["id"]: drug for drug in result["drugs"]}
    added = 0
    for drug_id, options in backfill["options_by_drug"].items():
        if drug_id not in by_id:
            raise ValueError(f"Backfill drug not in local catalog: {drug_id}")
        if not isinstance(options, list):
            raise ValueError(f"Invalid options for {drug_id}")
        existing = by_id[drug_id].get("dosage_options") or []
        by_key = {option_key(option): option for option in existing}
        for option in options:
            key = option_key(option)
            if key in by_key:
                if by_key[key] != option:
                    raise ValueError(
                        f"Local strength conflicts with backfill for {drug_id}: {key}"
                    )
                continue
            existing.append(copy.deepcopy(option))
            by_key[key] = option
            added += 1
        by_id[drug_id]["dosage_options"] = existing
    return result, added


def apply(
    path: Path,
    backfill_path: Path = BACKFILL_PATH,
    *,
    backup_dir: Path | None = None,
) -> tuple[int, Path | None]:
    payload = load_drugs_curation(path)
    backfill = json.loads(backfill_path.read_text(encoding="utf-8"))
    updated, count = merge(payload, backfill)
    if not count:
        return 0, None
    errors = validate_drugs_curation(path)
    if errors:
        raise ValueError("Local drug curation is invalid before merge")
    backup = (
        atomic_save_payload(updated, path=path, backup_dir=backup_dir)
        if backup_dir is not None
        else atomic_save_payload(updated, path=path)
    )
    return count, backup


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
    count, backup = apply(args.drugs)
    print(
        f"Added {count} source-linked options to {args.drugs}."
        + (f" Previous file: {backup}" if backup else " Already up to date.")
    )


if __name__ == "__main__":
    main()
