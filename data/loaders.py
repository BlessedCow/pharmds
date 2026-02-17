from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent


def load_transporters() -> dict[str, dict[str, Any]]:
    path = DATA_DIR / "transporters.json"
    raw = json.loads(path.read_text(encoding="utf-8"))

    out: dict[str, dict[str, Any]] = {}

    # Case 1: list of objects: [{"id": "...", "name": "...", "family": "..."}]
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                t_id = item.get("id")
                if not t_id:
                    continue
                out[t_id] = item
            elif isinstance(item, str):
                # list of ids only: ["P-gp", "BCRP"]
                out[item] = {"id": item, "name": item}
        return out

    # Case 2: dict mapping: {"P-gp": "P-glycoprotein"} OR {"P-gp": {"id":...}}
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                t_id = v.get("id") or k
                v2 = dict(v)
                v2["id"] = t_id
                out[t_id] = v2
            elif isinstance(v, str):
                out[k] = {"id": k, "name": v}
            else:
                out[k] = {"id": k, "name": k}
        return out

    return out


def load_drugs_curation(path: Path | None = None) -> dict[str, Any]:
    """Load data/curation/drugs.json (v1).

    This is the source of truth for drug assertions used to seed the SQLite DB.
    """
    if path is None:
        path = DATA_DIR / "curation" / "drugs.json"
    return json.loads(path.read_text(encoding="utf-8"))
