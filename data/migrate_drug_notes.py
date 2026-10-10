"""Update notes for existing SQLite drug rows from drug curation."""

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
    with conn:
        count = 0
        for drug in load_drugs_curation(path)["drugs"]:
            result = conn.execute(
                "UPDATE drug SET notes=? WHERE id=? AND notes IS NOT ?",
                (drug.get("notes"), drug["id"], drug.get("notes")),
            )
            count += result.rowcount
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
    print(f"Updated {count} existing drug notes in {args.db}")


if __name__ == "__main__":
    main()
