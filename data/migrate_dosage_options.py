"""Load sourced reference strengths into an existing PharmDS SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from data.curation.validate import validate_drugs_curation
from data.loaders import load_drugs_curation
from data.seed_sqlite import DB_PATH, connect


def migrate(conn: sqlite3.Connection, *, curation_path: Path | None = None) -> int:
    path = curation_path or Path(__file__).parent / "curation" / "drugs.json"
    errors = validate_drugs_curation(path)
    if errors:
        raise ValueError(
            "Invalid drug curation: "
            + "; ".join(f"{error.path}: {error.message}" for error in errors)
        )
    drugs = load_drugs_curation(path)["drugs"]
    with conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(drug_dosage_option)")
        }
        if not columns:
            raise ValueError(
                "Missing drug_dosage_option table; seed the database first"
            )
        for column in ("product_name", "composition", "source_url"):
            if column not in columns:
                conn.execute(f"ALTER TABLE drug_dosage_option ADD COLUMN {column} TEXT")
        count = 0
        for drug in drugs:
            for option in drug.get("dosage_options", []) or []:
                conn.execute(
                    "INSERT INTO drug_dosage_option ("
                    "drug_id,route,release_type,dosage_form,strength_value,strength_unit,"
                    "product_name,composition,source_url) VALUES (?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(drug_id,route,release_type,dosage_form,"
                    "strength_value,strength_unit) DO UPDATE SET "
                    "product_name=excluded.product_name,composition=excluded.composition,"
                    "source_url=excluded.source_url",
                    (
                        drug["id"],
                        option["route"],
                        option["release_type"],
                        option["dosage_form"],
                        option["strength_value"],
                        option["strength_unit"],
                        option.get("product_name"),
                        option.get("composition"),
                        option.get("source_url"),
                    ),
                )
                count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f"Database not found: {args.db}")
    conn = connect(args.db)
    try:
        count = migrate(conn)
    finally:
        conn.close()
    print(f"Loaded {count} sourced reference strength options into {args.db}")


if __name__ == "__main__":
    main()
