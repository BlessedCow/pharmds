from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from core.pd_effect_families import PD_EFFECT_RULE_FAMILIES

DRUGS_PATH = Path("data/curation/drugs.json")
RULE_DIR = Path("rules/rule_defs")

DOCUMENTED_PD_EFFECT_GAPS = {
    "cholinergic_modulation": (
        "Broad mechanistic tag; pairwise clinical meaning requires more "
        "specific logic before a generic rule is appropriate."
    ),
    "hypersensitivity_risk": (
        "Hypersensitivity is not assumed to be generically additive across "
        "unrelated agents."
    ),
    "nAChR_antagonism": (
        "Mechanistic receptor tag; additive clinical interpretation needs "
        "specific rule design."
    ),
    "renal_function": (
        "Contextual physiologic tag; pairwise interpretation requires "
        "direction and mechanism rather than simple overlap."
    ),
}


@dataclass(frozen=True)
class PdCoverageAudit:
    curated_effects: frozenset[str]
    direct_rule_effects: frozenset[str]
    explicit_pair_effects: frozenset[str]
    mapped_effects: dict[str, str]
    documented_gaps: dict[str, str]
    drugs_by_effect: dict[str, tuple[str, ...]]

    @property
    def covered_curated_effects(self) -> frozenset[str]:
        return frozenset(
            effect_id
            for effect_id in self.curated_effects
            if effect_id in self.direct_rule_effects
            or effect_id in self.explicit_pair_effects
            or effect_id in self.mapped_effects
        )

    @property
    def uncovered_curated_effects(self) -> frozenset[str]:
        return self.curated_effects - self.covered_curated_effects

    @property
    def undocumented_effects(self) -> frozenset[str]:
        return self.uncovered_curated_effects - set(self.documented_gaps)


def _load_drugs(path: Path = DRUGS_PATH) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["drugs"]


def _load_rules(rule_dir: Path = RULE_DIR) -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(rule_dir.glob("*.json"))
    ]


def build_pd_coverage_audit(
    *,
    drugs_path: Path = DRUGS_PATH,
    rule_dir: Path = RULE_DIR,
) -> PdCoverageAudit:
    drugs = _load_drugs(drugs_path)
    rules = _load_rules(rule_dir)

    drugs_by_effect: dict[str, list[str]] = defaultdict(list)

    for drug in drugs:
        for effect in drug.get("pd_effects", []) or []:
            effect_id = effect.get("effect_id")

            if effect_id:
                drugs_by_effect[effect_id].append(drug["id"])

    curated_effects = frozenset(drugs_by_effect)

    direct_rule_effects = frozenset(
        rule["logic"]["pd_overlap"]["effect_id"]
        for rule in rules
        if rule.get("domain") == "PD"
        and "pd_overlap" in rule.get("logic", {})
    )

    explicit_pair_effects = frozenset(
        rule["logic"]["effect_id"]
        for rule in rules
        if rule.get("domain") == "PD"
        and "drug_pair" in rule.get("logic", {})
        and isinstance(rule.get("logic", {}).get("effect_id"), str)
    )

    mapped_effects = {
        source_effect: target_effect
        for source_effect, target_effect in PD_EFFECT_RULE_FAMILIES.items()
        if source_effect in curated_effects
        and (
            target_effect in direct_rule_effects
            or target_effect in explicit_pair_effects
        )
    }

    documented_gaps = {
        effect_id: reason
        for effect_id, reason in DOCUMENTED_PD_EFFECT_GAPS.items()
        if effect_id in curated_effects
    }

    return PdCoverageAudit(
        curated_effects=curated_effects,
        direct_rule_effects=direct_rule_effects,
        explicit_pair_effects=explicit_pair_effects,
        mapped_effects=mapped_effects,
        documented_gaps=documented_gaps,
        drugs_by_effect={
            effect_id: tuple(sorted(drug_ids))
            for effect_id, drug_ids in drugs_by_effect.items()
        },
    )


def render_markdown(audit: PdCoverageAudit) -> str:
    lines = [
        "# PD Effect Coverage Audit",
        "",
        "This audit compares curated drug PD effects with generic PD overlap "
        "rules, explicit PD pair rules, concept-family mappings, and "
        "documented coverage gaps.",
        "",
        "## Summary",
        "",
        f"- Curated PD effect IDs: {len(audit.curated_effects)}",
        (
            "- Direct generic-rule coverage: "
            f"{len(audit.curated_effects & audit.direct_rule_effects)}"
        ),
        f"- Concept-family mappings: {len(audit.mapped_effects)}",
        f"- Explicit pair effect IDs: {len(audit.explicit_pair_effects)}",
        f"- Documented uncovered concepts: {len(audit.documented_gaps)}",
        f"- Undocumented curated effects: {len(audit.undocumented_effects)}",
        "",
        "## Concept-family mappings",
        "",
    ]

    for source_effect, target_effect in sorted(audit.mapped_effects.items()):
        lines.append(f"- `{source_effect}` -> `{target_effect}`")

    lines.extend(
        [
            "",
            "## Documented coverage gaps",
            "",
        ]
    )

    for effect_id, reason in sorted(audit.documented_gaps.items()):
        drugs = ", ".join(audit.drugs_by_effect.get(effect_id, ()))
        lines.append(f"### `{effect_id}`")
        lines.append("")
        lines.append(reason)
        lines.append("")
        lines.append(f"Curated drugs: {drugs or 'None'}")
        lines.append("")

    lines.extend(
        [
            "## Directly covered curated effects",
            "",
        ]
    )

    for effect_id in sorted(
        audit.curated_effects & audit.direct_rule_effects
    ):
        lines.append(f"- `{effect_id}`")

    lines.extend(
        [
            "",
            "## Explicit pair effect coverage",
            "",
        ]
    )

    if audit.explicit_pair_effects:
        for effect_id in sorted(audit.explicit_pair_effects):
            lines.append(f"- `{effect_id}`")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Undocumented effects",
            "",
        ]
    )

    if audit.undocumented_effects:
        for effect_id in sorted(audit.undocumented_effects):
            lines.append(f"- `{effect_id}`")
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    audit = build_pd_coverage_audit()
    print(render_markdown(audit), end="")


if __name__ == "__main__":
    main()
