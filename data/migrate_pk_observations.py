"""Add curated PK observation tables to an existing database in place."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from data.curation.pk_observations import DEFAULT_PATH, load_pk_curation
from data.pk_observation_seed import upsert_pk_observations
from data.seed_sqlite import DB_PATH, apply_schema, connect


def migrate(
    conn: sqlite3.Connection,
    *,
    curation_path: Path = DEFAULT_PATH,
) -> None:
    sources, observations = load_pk_curation(curation_path)
    apply_schema(conn)
    with conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(pk_observation)")
        }
        if "math_eligible" not in columns:
            conn.execute(
                "ALTER TABLE pk_observation ADD COLUMN math_eligible "
                "INTEGER NOT NULL DEFAULT 0 CHECK (math_eligible IN (0, 1))"
            )
        upsert_pk_observations(conn, sources, observations)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    if not args.db.is_file():
        parser.error(f"Database not found: {args.db}")
    conn = connect(args.db)
    try:
        migrate(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
