"""Import a sourced catalog batch, preserving local records and reporting conflicts."""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path

from data.curation.pk_observations import load_pk_curation
from data.curation.validate import validate_drugs_curation
from data.loaders import load_drugs_curation
from tools.curation_gui import atomic_save_payload
from tools.pk_curation_editor import save_pk_payload

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/curation/catalog_expansion_2026_10.json"
PK_MANIFEST = ROOT / "data/curation/pk_expansion_2026_10.json"


def _identity(field: str, row: dict) -> tuple:
    if field == "enzymes":
        return (row["enzyme_id"], row["role"])
    if field == "transporters":
        return (row["transporter_id"], row["role"])
    if field == "pd_effects":
        return (row["effect_id"], row["direction"])
    if field == "dosage_options":
        return (
            row["route"],
            row["release_type"],
            row["dosage_form"].casefold(),
            float(row["strength_value"]),
            row["strength_unit"].casefold(),
        )
    raise ValueError(field)


def merge_drugs(payload: dict, manifest: dict) -> tuple[dict, int, list[str]]:
    if manifest.get("version") != 1 or not isinstance(manifest.get("drugs"), list):
        raise ValueError("Invalid catalog expansion")
    result = copy.deepcopy(payload)
    by_id = {drug["id"]: drug for drug in result["drugs"]}
    added = 0
    conflicts: list[str] = []
    for incoming in manifest["drugs"]:
        drug_id = incoming["id"]
        if drug_id not in by_id:
            result["drugs"].append(copy.deepcopy(incoming))
            by_id[drug_id] = result["drugs"][-1]
            added += 1
            continue
        current = by_id[drug_id]
        for key in ("generic_name", "drug_class", "therapeutic_index", "notes"):
            if not current.get(key):
                current[key] = copy.deepcopy(incoming[key])
            elif current[key] != incoming[key]:
                conflicts.append(f"{drug_id}.{key}: kept local value")
        for key in ("aliases", "brand_names"):
            local = current.setdefault(key, [])
            for value in incoming[key]:
                if value.casefold() not in {x.casefold() for x in local}:
                    local.append(value)
        local_parameters = current.setdefault("parameters", {})
        for key, value in incoming["parameters"].items():
            if key not in local_parameters:
                local_parameters[key] = value
            elif local_parameters[key] != value:
                conflicts.append(f"{drug_id}.parameters.{key}: kept local value")
        local_forms = current.setdefault("formulations", [])
        for form in incoming["formulations"]:
            matching = next(
                (f for f in local_forms if f["route"] == form["route"]), None
            )
            if matching is None:
                local_forms.append(copy.deepcopy(form))
            else:
                for release in form["release_types"]:
                    if release not in matching["release_types"]:
                        matching["release_types"].append(release)
        current["release_types"] = list(
            dict.fromkeys(rel for form in local_forms for rel in form["release_types"])
        )
        for field in ("enzymes", "transporters", "pd_effects", "dosage_options"):
            local = current.setdefault(field, [])
            index = {_identity(field, row): row for row in local}
            for row in incoming[field]:
                key = _identity(field, row)
                if key not in index:
                    local.append(copy.deepcopy(row))
                    index[key] = local[-1]
                elif index[key] != row:
                    conflicts.append(f"{drug_id}.{field}.{key}: kept local value")
    return result, added, conflicts


def merge_pk(payload: dict, manifest: dict) -> tuple[dict, int]:
    if (
        manifest.get("version") != 1
        or not isinstance(manifest.get("sources"), list)
        or not isinstance(manifest.get("observations"), list)
    ):
        raise ValueError("Invalid PK expansion")
    result = copy.deepcopy(payload)
    count = 0
    for collection in ("sources", "observations"):
        by_id = {row["id"]: row for row in result[collection]}
        for row in manifest[collection]:
            if row["id"] in by_id:
                if by_id[row["id"]] != row:
                    raise ValueError(f"Local PK {collection} conflict: {row['id']}")
            else:
                result[collection].append(copy.deepcopy(row))
                count += collection == "observations"
    return result, count


def _validate_pair(drugs: dict, pk: dict) -> None:
    with tempfile.TemporaryDirectory() as temp:
        dp, pp = Path(temp) / "drugs.json", Path(temp) / "pk.json"
        dp.write_text(json.dumps(drugs), encoding="utf-8")
        pp.write_text(json.dumps(pk), encoding="utf-8")
        errors = validate_drugs_curation(dp)
        if errors:
            raise ValueError(
                "Catalog validation failed: "
                + "; ".join(f"{e.path}: {e.message}" for e in errors[:8])
            )
        load_pk_curation(pp, drugs_path=dp)


def apply(
    drugs_path: Path, pk_path: Path, *, backup_dir: Path | None = None
) -> tuple[int, int, list[str]]:
    drugs = load_drugs_curation(drugs_path)
    pk = json.loads(pk_path.read_text(encoding="utf-8"))
    updated_drugs, added, conflicts = merge_drugs(
        drugs, json.loads(MANIFEST.read_text(encoding="utf-8"))
    )
    updated_pk, observations = merge_pk(
        pk, json.loads(PK_MANIFEST.read_text(encoding="utf-8"))
    )
    _validate_pair(updated_drugs, updated_pk)
    if updated_drugs != drugs:
        atomic_save_payload(
            updated_drugs,
            path=drugs_path,
            **({"backup_dir": backup_dir} if backup_dir else {}),
        )
    if updated_pk != pk:
        save_pk_payload(
            updated_pk, path=pk_path, drugs_path=drugs_path, backup_dir=backup_dir
        )
    return added, observations, conflicts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drugs", type=Path, default=ROOT / "data/curation/drugs.json")
    parser.add_argument(
        "--pk", type=Path, default=ROOT / "data/curation/pk_observations.json"
    )
    parser.add_argument("--backup-dir", type=Path, default=None)
    args = parser.parse_args()
    added, observations, conflicts = apply(
        args.drugs, args.pk, backup_dir=args.backup_dir
    )
    print(f"Added {added} catalog entries and {observations} PK observations.")
    if conflicts:
        print("Preserved local differences:\n" + "\n".join(conflicts))


if __name__ == "__main__":
    main()
