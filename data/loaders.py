from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DATA_DIR = Path(__file__).parent

def load_transporters() -> Dict[str, Dict[str, Any]]:
    path = DATA_DIR / "transporters.json"
    raw = json.loads(path.read_text(encoding="utf-8"))

    out: Dict[str, Dict[str, Any]] = {}

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