from __future__ import annotations

import json
from pathlib import Path

from rules.validate_rules import (
    _load_transporter_families,
    _load_transporter_ids,
    validate_rule,
)


def test_all_rule_definitions_validate() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    rule_dir = base_dir / "rules" / "rule_defs"

    transporter_ids = _load_transporter_ids(base_dir)
    transporter_families = _load_transporter_families(base_dir)

    errors = []

    for path in sorted(rule_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(
            validate_rule(
                path=path,
                raw=raw,
                transporter_ids=transporter_ids,
                transporter_families=transporter_families,
            )
        )

    assert errors == []