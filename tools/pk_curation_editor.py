"""Validated editing helpers for sourced PK data in the medication GUI."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from data.curation.pk_observations import DEFAULT_PATH, load_pk_curation


def read_pk_payload(path: Path = DEFAULT_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def replace_entry(payload: dict, collection: str, entry: dict) -> None:
    """Stage one source or observation by stable ID without touching other rows."""
    if collection not in {"sources", "observations"}:
        raise ValueError("Unsupported PK collection")
    rows = payload[collection]
    index = next((i for i, row in enumerate(rows) if row["id"] == entry["id"]), None)
    if index is None:
        rows.append(entry)
    else:
        rows[index] = entry


def save_pk_payload(
    payload: dict,
    *,
    path: Path = DEFAULT_PATH,
    drugs_path: Path | None = None,
    backup_dir: Path | None = None,
    expected_bytes: bytes | None = None,
) -> Path:
    """Validate staged data and preserve the previous file before replacement."""
    path = path.resolve()
    if expected_bytes is not None and path.read_bytes() != expected_bytes:
        raise ValueError("PK curation changed on disk. Reopen the GUI before saving.")
    backup_dir = backup_dir or Path.home() / ".pharmds" / "curation_backups"
    fd, name = tempfile.mkstemp(
        prefix=f"{path.stem}.", suffix=".tmp.json", dir=path.parent
    )
    os.close(fd)
    temp_path = Path(name)
    try:
        temp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        load_pk_curation(temp_path, drugs_path=drugs_path)
        if expected_bytes is not None and path.read_bytes() != expected_bytes:
            raise ValueError(
                "PK curation changed on disk. Reopen the GUI before saving."
            )
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = backup_dir / f"pk_observations-{stamp}.json"
        shutil.copy2(path, backup_path)
        os.replace(temp_path, path)
        return backup_path
    finally:
        temp_path.unlink(missing_ok=True)
