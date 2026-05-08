from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Keep these in sync with core.enums
ALLOWED_DOMAINS = {"PK", "PD"}
ALLOWED_SEVERITIES = {"info", "caution", "major", "contraindicated"}
ALLOWED_RULE_CLASSES = {"info", "caution", "adjust_monitor", "avoid"}
ALLOWED_ROLES = {"substrate", "inhibitor", "inducer"}
ALLOWED_STRENGTHS = {"weak", "moderate", "strong"}
ALLOWED_PD_MAGNITUDES = {"low", "medium", "high"}
ALLOWED_TI = {"wide", "moderate", "narrow"}

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

PRIMARY_LOGIC_KEYS = {"enzyme", "transporter", "pd_overlap", "drug_pair"}

# Allowed placeholders in templates and rationale strings.
ALLOWED_PLACEHOLDERS = {
    "A_name",
    "B_name",
    "enzyme_id",
    "transporter_id",
    "transporter_family",
    "effect_id",
}

PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")


@dataclass
class RuleError:
    file: str
    message: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("JSON root must be an object")

    return data


def _load_transporters(base_dir: Path) -> dict[str, Any]:
    path = base_dir / "data" / "transporters.json"
    if not path.exists():
        return {}

    data = _load_json(path)
    if not isinstance(data, dict):
        raise ValueError(
            "data/transporters.json must be a JSON object mapping transporter_id -> metadata"
        )

    return data


def _load_transporter_ids(base_dir: Path) -> set[str]:
    """
    Loads canonical transporter IDs from pharmds/data/transporters.json.
    Returns a set of keys like {"P-gp", "OATP1B1", "BCRP"}.
    """
    return set(_load_transporters(base_dir).keys())


def _load_transporter_families(base_dir: Path) -> set[str]:
    """
    Loads canonical transporter families from pharmds/data/transporters.json.
    Returns values like {"ABCB1", "ABCG2", "OATP"} when present.
    """
    families: set[str] = set()
    for meta in _load_transporters(base_dir).values():
        if isinstance(meta, dict):
            family = meta.get("family")
            if isinstance(family, str) and family.strip():
                families.add(family)
    return families


def _find_placeholders(text: str) -> set[str]:
    return {m.group(1) for m in PLACEHOLDER_RE.finditer(text or "")}


def _check_string(
    errors: list[RuleError], path: Path, raw: dict[str, Any], key: str
) -> None:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(RuleError(path.name, f"{key} must be a non-empty string"))


def _check_string_list(
    errors: list[RuleError], path: Path, value: Any, label: str
) -> None:
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        errors.append(RuleError(path.name, f"{label} must be a list of strings"))


def _check_role(
    errors: list[RuleError],
    path: Path,
    block: dict[str, Any],
    block_name: str,
    role_key: str,
) -> None:
    role_val = block.get(role_key)
    if role_val not in ALLOWED_ROLES:
        errors.append(
            RuleError(
                path.name,
                f"logic.{block_name}.{role_key} must be one of {sorted(ALLOWED_ROLES)} "
                f"(got: {role_val})",
            )
        )


def _check_strength_fields(
    errors: list[RuleError], path: Path, block: dict[str, Any], block_name: str
) -> None:
    strength = block.get("B_strength")
    if strength is not None and strength not in ALLOWED_STRENGTHS:
        errors.append(
            RuleError(
                path.name,
                f"logic.{block_name}.B_strength must be one of {sorted(ALLOWED_STRENGTHS)} "
                f"(got: {strength})",
            )
        )

    strength_in = block.get("B_strength_in")
    if strength_in is not None:
        if not isinstance(strength_in, list) or any(
            x not in ALLOWED_STRENGTHS for x in strength_in
        ):
            errors.append(
                RuleError(
                    path.name,
                    f"logic.{block_name}.B_strength_in must be a list containing only "
                    f"{sorted(ALLOWED_STRENGTHS)}",
                )
            )


def validate_rule(
    path: Path,
    raw: dict[str, Any],
    transporter_ids: set[str],
    transporter_families: set[str] | None = None,
) -> list[RuleError]:
    errors: list[RuleError] = []
    transporter_families = transporter_families or set()

    missing = REQUIRED_TOP_KEYS - set(raw.keys())
    if missing:
        errors.append(RuleError(path.name, f"Missing required keys: {sorted(missing)}"))
        return errors

    for key in (
        "id",
        "name",
        "domain",
        "severity",
        "rule_class",
        "explanation_template",
    ):
        _check_string(errors, path, raw, key)

    if raw.get("domain") not in ALLOWED_DOMAINS:
        errors.append(
            RuleError(
                path.name,
                f"Invalid domain: {raw.get('domain')} (allowed: {sorted(ALLOWED_DOMAINS)})",
            )
        )

    if raw.get("severity") not in ALLOWED_SEVERITIES:
        errors.append(
            RuleError(
                path.name,
                f"Invalid severity: {raw.get('severity')} "
                f"(allowed: {sorted(ALLOWED_SEVERITIES)})",
            )
        )

    if raw.get("rule_class") not in ALLOWED_RULE_CLASSES:
        errors.append(
            RuleError(
                path.name,
                f"Invalid rule_class: {raw.get('rule_class')} "
                f"(allowed: {sorted(ALLOWED_RULE_CLASSES)})",
            )
        )

    _check_string_list(errors, path, raw.get("actions"), "actions")

    tags = raw.get("tags", [])
    if tags is not None:
        _check_string_list(errors, path, tags, "tags")

    references = raw.get("references", [])
    if references is not None:
        if not isinstance(references, list) or any(
            not isinstance(x, dict) for x in references
        ):
            errors.append(RuleError(path.name, "references must be a list of objects"))

    logic = raw.get("logic")
    if not isinstance(logic, dict):
        errors.append(RuleError(path.name, "logic must be an object"))
        return errors

    primary_keys = PRIMARY_LOGIC_KEYS & set(logic.keys())
    if len(primary_keys) != 1:
        errors.append(
            RuleError(
                path.name,
                "logic must include exactly one of enzyme/transporter/pd_overlap/drug_pair "
                f"(found: {sorted(primary_keys)})",
            )
        )

    unknown_ph = (
        _find_placeholders(raw.get("explanation_template", ""))
        - ALLOWED_PLACEHOLDERS
    )

    rationale = logic.get("rationale", [])
    if rationale is not None:
        if not isinstance(rationale, list) or any(
            not isinstance(x, str) for x in rationale
        ):
            errors.append(RuleError(path.name, "logic.rationale must be a list of strings"))
        else:
            for line in rationale:
                unknown_ph |= _find_placeholders(line) - ALLOWED_PLACEHOLDERS

    if unknown_ph:
        errors.append(RuleError(path.name, f"Unknown placeholders: {sorted(unknown_ph)}"))

    if "enzyme" in logic:
        enz = logic["enzyme"]
        if not isinstance(enz, dict):
            errors.append(RuleError(path.name, "logic.enzyme must be an object"))
        else:
            for k in ("id", "A_role", "B_role"):
                if k not in enz:
                    errors.append(RuleError(path.name, f"logic.enzyme missing {k}"))

            eid = enz.get("id")
            if not isinstance(eid, str) or not eid.strip():
                errors.append(RuleError(path.name, "logic.enzyme.id must be a non-empty string"))

            for role_key in ("A_role", "B_role"):
                if role_key in enz:
                    _check_role(errors, path, enz, "enzyme", role_key)

            _check_strength_fields(errors, path, enz, "enzyme")

    if "transporter" in logic:
        tr = logic["transporter"]
        if not isinstance(tr, dict):
            errors.append(RuleError(path.name, "logic.transporter must be an object"))
        else:
            for k in ("A_role", "B_role"):
                if k not in tr:
                    errors.append(RuleError(path.name, f"logic.transporter missing {k}"))

            tid = tr.get("id")
            family = tr.get("family")

            if tid is None and family is None:
                errors.append(
                    RuleError(
                        path.name,
                        "logic.transporter must include either id or family",
                    )
                )

            if tid is not None:
                if not isinstance(tid, str) or not tid.strip():
                    errors.append(
                        RuleError(
                            path.name,
                            "logic.transporter.id must be a non-empty string",
                        )
                    )
                elif transporter_ids and tid not in transporter_ids:
                    errors.append(
                        RuleError(
                            path.name,
                            f"Unknown transporter id: {tid} "
                            f"(known: {sorted(transporter_ids)})",
                        )
                    )

            if family is not None:
                if not isinstance(family, str) or not family.strip():
                    errors.append(
                        RuleError(
                            path.name,
                            "logic.transporter.family must be a non-empty string",
                        )
                    )
                elif transporter_families and family not in transporter_families:
                    errors.append(
                        RuleError(
                            path.name,
                            f"Unknown transporter family: {family} "
                            f"(known: {sorted(transporter_families)})",
                        )
                    )

            for role_key in ("A_role", "B_role"):
                if role_key in tr:
                    _check_role(errors, path, tr, "transporter", role_key)

            _check_strength_fields(errors, path, tr, "transporter")

    if "pd_overlap" in logic:
        pd = logic["pd_overlap"]
        if not isinstance(pd, dict):
            errors.append(RuleError(path.name, "logic.pd_overlap must be an object"))
        else:
            effect_id = pd.get("effect_id")
            if not isinstance(effect_id, str) or not effect_id.strip():
                errors.append(
                    RuleError(
                        path.name,
                        "logic.pd_overlap.effect_id must be a non-empty string",
                    )
                )

            min_magnitude = pd.get("min_magnitude")
            if (
                min_magnitude is not None
                and min_magnitude not in ALLOWED_PD_MAGNITUDES
            ):
                errors.append(
                    RuleError(
                        path.name,
                        "logic.pd_overlap.min_magnitude must be one of "
                        f"{sorted(ALLOWED_PD_MAGNITUDES)} (got: {min_magnitude})",
                    )
                )

    if "drug_pair" in logic:
        pair = logic["drug_pair"]
        if not isinstance(pair, dict):
            errors.append(RuleError(path.name, "logic.drug_pair must be an object"))
        else:
            for k in ("a", "b"):
                value = pair.get(k)
                if not isinstance(value, str) or not value.strip():
                    errors.append(
                        RuleError(
                            path.name,
                            f"logic.drug_pair.{k} must be a non-empty string",
                        )
                    )

    a_ti = logic.get("A_ti")
    if a_ti is not None and a_ti not in ALLOWED_TI:
        errors.append(
            RuleError(
                path.name,
                f"logic.A_ti must be one of {sorted(ALLOWED_TI)} (got: {a_ti})",
            )
        )

    for key in ("A_name_is", "B_name_is"):
        value = logic.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(RuleError(path.name, f"logic.{key} must be a non-empty string"))

    for key in ("A_name_not_is", "B_name_not_is"):
        value = logic.get(key)
        if value is not None:
            if isinstance(value, str):
                continue
            if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
                errors.append(
                    RuleError(
                        path.name,
                        f"logic.{key} must be a string or list of strings",
                    )
                )

    patient_flag = logic.get("requires_patient_flag")
    if patient_flag is not None and (
        not isinstance(patient_flag, str) or not patient_flag.strip()
    ):
        errors.append(
            RuleError(
                path.name,
                "logic.requires_patient_flag must be a non-empty string",
            )
        )

    return errors


def main() -> int:
    base_dir = Path(__file__).resolve().parents[1]
    transporter_ids = _load_transporter_ids(base_dir)
    transporter_families = _load_transporter_families(base_dir)
    rule_dir = base_dir / "rules" / "rule_defs"

    if not rule_dir.exists():
        print(f"Rule directory not found: {rule_dir}")
        return 2

    all_errors: list[RuleError] = []
    files = sorted(rule_dir.glob("*.json"))
    if not files:
        print(f"No rule JSON files found in: {rule_dir}")
        return 2

    for p in files:
        try:
            raw = _load_json(p)
            all_errors.extend(
                validate_rule(p, raw, transporter_ids, transporter_families)
            )
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
