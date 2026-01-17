from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set, Optional, Tuple

#Keep these in sync with core.enums
ALLOWED_DOMAINS = {"PK", "PD"}
ALLOWED_SEVERITIES = {"info", "caution", "major", "contraindicated"}
ALLOWED_RULE_CLASSES = {"info", "caution", "adjust_monitor", "avoid"}

REQUIRED_TOP_KEYS = {
    "id",
    "name",
    "domain",
    "severity",
    "rule_class",
    "actions",
    "logic",
    "explanation_template",
}

# Allowed placeholder in templates and rationaele
ALLOWED_PLACEHOLDERS = {
    "A_name",
    "B_name",
    "enzyme_id",
    "transporter_id",
    "effect_id",
}

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")

@dataclass
class RuleError:
    file: str
    message: str


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON: {e}") from e

def _find_placeholders(text: str) -> Set[str]:
    return {m.group(1) for m in PLACEHOLDER_RE.finditer(text or "")}


def validate_rule(path: Path, raw: Dict[str, Any]) -> List[RuleError]:
    errors: List[RuleError] = []

    # Required top-level keys
    missing = REQUIRED_TOP_KEYS - set(raw.keys())
    if missing:
        errors.append(RuleError(path.name, f"Missing required keys: {sorted(missing)}"))
        return errors  # cannot safely continue

    # Enums
    if raw["domain"] not in ALLOWED_DOMAINS:
        errors.append(RuleError(path.name, f"Invalid domain: {raw['domain']} (allowed: {sorted(ALLOWED_DOMAINS)})"))

    if raw["severity"] not in ALLOWED_SEVERITIES:
        errors.append(RuleError(path.name, f"Invalid severity: {raw['severity']} (allowed: {sorted(ALLOWED_SEVERITIES)})"))

    if raw["rule_class"] not in ALLOWED_RULE_CLASSES:
        errors.append(RuleError(path.name, f"Invalid rule_class: {raw['rule_class']} (allowed: {sorted(ALLOWED_RULE_CLASSES)})"))

    # actions must be list[str]
    actions = raw.get("actions")
    if not isinstance(actions, list) or any(not isinstance(x, str) for x in actions):
        errors.append(RuleError(path.name, "actions must be a list of strings"))

    # logic: must include exactly one of enzyme/transporter/pd_overlap for v0
    logic = raw.get("logic")
    if not isinstance(logic, dict):
        errors.append(RuleError(path.name, "logic must be an object"))
        return errors

    keys = {"enzyme", "transporter", "pd_overlap"} & set(logic.keys())
    if len(keys) != 1:
        errors.append(
            RuleError(
                path.name,
                f"logic must include exactly one of enzyme/transporter/pd_overlap (found: {sorted(keys)})",
            )
        )

    # placeholder checks in explanation_template + rationale lines
    unknown_ph = set()
    unknown_ph |= _find_placeholders(raw.get("explanation_template", "")) - ALLOWED_PLACEHOLDERS

    rationale = logic.get("rationale", [])
    if not isinstance(rationale, list) or any(not isinstance(x, str) for x in rationale):
        errors.append(RuleError(path.name, "logic.rationale must be a list of strings"))
    else:
        for line in rationale:
            unknown_ph |= _find_placeholders(line) - ALLOWED_PLACEHOLDERS

    if unknown_ph:
        errors.append(RuleError(path.name, f"Unknown placeholders: {sorted(unknown_ph)}"))

    # Basic logic shape checks
    if "enzyme" in logic:
        enz = logic["enzyme"]
        if not isinstance(enz, dict):
            errors.append(RuleError(path.name, "logic.enzyme must be an object"))
        else:
            for k in ("id", "A_role", "B_role"):
                if k not in enz:
                    errors.append(RuleError(path.name, f"logic.enzyme missing {k}"))

    if "transporter" in logic:
        tr = logic["transporter"]
        if not isinstance(tr, dict):
            errors.append(RuleError(path.name, "logic.transporter must be an object"))
        else:
            for k in ("id", "A_role", "B_role"):
                if k not in tr:
                    errors.append(RuleError(path.name, f"logic.transporter missing {k}"))

    if "pd_overlap" in logic:
        pd = logic["pd_overlap"]
        if not isinstance(pd, dict):
            errors.append(RuleError(path.name, "logic.pd_overlap must be an object"))
        else:
            if "effect_id" not in pd:
                errors.append(RuleError(path.name, "logic.pd_overlap missing effect_id"))

    return errors


def main() -> int:
    base_dir = Path(__file__).resolve().parents[1]
    rule_dir = base_dir / "rules" / "rule_defs"

    if not rule_dir.exists():
        print(f"Rule directory not found: {rule_dir}")
        return 2

    all_errors: List[RuleError] = []
    files = sorted(rule_dir.glob("*.json"))
    if not files:
        print(f"No rule JSON files found in: {rule_dir}")
        return 2

    for p in files:
        try:
            raw = _load_json(p)
            all_errors.extend(validate_rule(p, raw))
        except Exception as e:
            all_errors.append(RuleError(p.name, str(e)))

    if all_errors:
        print("Rule validation failed:\n")
        for err in all_errors:
            print(f"- {err.file}: {err.message}")
        return 1

    print(f"Rule validation passed ({len(files)} rules).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())