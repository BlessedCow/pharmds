from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is on sys.path so tests can import `app`, `rules`, etc.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_sessionstart(session):
    """Rebuild the SQLite DB from curation before running tests.

    CI previously relied on a committed pharmds.sqlite3 artifact, which can drift.
    Seeding on session start keeps tests aligned with the curation source of truth.
    """
    from data.seed_sqlite import DB_PATH, apply_schema, connect, seed

    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = connect(DB_PATH)
    apply_schema(conn)
    seed(conn)
    conn.commit()
    conn.close()
