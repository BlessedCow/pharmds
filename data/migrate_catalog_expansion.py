"""Seed only the reviewed catalog expansion into an existing PharmDS database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from data.seed_sqlite import DB_PATH, apply_schema, connect, seed
from tools.apply_catalog_expansion import MANIFEST


def migrate(db_path: Path, *, backup_dir: Path | None = None) -> Path:
    if not db_path.is_file():
        raise FileNotFoundError(db_path)
    backup_dir = backup_dir or db_path.parent / "curation_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = (
        backup_dir / f"{db_path.stem}-{datetime.now():%Y%m%d-%H%M%S-%f}.sqlite3"
    )
    conn = connect(db_path)
    try:
        with sqlite3.connect(backup_path) as backup:
            conn.backup(backup)
        ids = {
            drug["id"]
            for drug in json.loads(MANIFEST.read_text(encoding="utf-8"))["drugs"]
        }
        with conn:
            apply_schema(conn)
            seed(conn, only_drug_ids=ids)
    finally:
        conn.close()
    return backup_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--backup-dir", type=Path)
    args = parser.parse_args()
    path = migrate(args.db, backup_dir=args.backup_dir)
    print(
        f"Seeded catalog expansion and sourced PK observations. Database backup: {path}"
    )


if __name__ == "__main__":
    main()
