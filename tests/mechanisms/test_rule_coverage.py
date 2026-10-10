from __future__ import annotations

import json
from pathlib import Path

from core.constants import TRANSPORTER_PGP
from core.mechanisms.rule_coverage import CURATED_PD_RULES, CURATED_PK_RULES

RULE_DIR = Path(__file__).resolve().parents[2] / "rules" / "rule_defs"


def test_pd_reconciliation_ids_match_single_effect_rule_definitions() -> None:
    for rule_id, effect_id in CURATED_PD_RULES.items():
        path = next(
            path
            for path in RULE_DIR.glob("*.json")
            if json.loads(path.read_text(encoding="utf-8"))["id"] == rule_id
        )
        rule = json.loads(path.read_text(encoding="utf-8"))
        assert rule["domain"] == "PD", rule_id
        assert rule["logic"]["pd_overlap"]["effect_id"] == effect_id, rule_id
        assert set(rule["logic"]) - {"rationale"} == {"pd_overlap"}, rule_id


def test_pk_reconciliation_ids_match_curated_roles_and_targets() -> None:
    rules = {
        rule["id"]: rule
        for path in RULE_DIR.glob("*.json")
        if (rule := json.loads(path.read_text(encoding="utf-8")))
    }
    for rule_id, (candidate_type, target, input_key) in CURATED_PK_RULES.items():
        rule = rules[rule_id]
        assert rule["domain"] == "PK", rule_id
        assert input_key in {"enzyme_id", "transporter_family"}
        block = rule["logic"]["enzyme" if input_key == "enzyme_id" else "transporter"]
        assert block["A_role"] == "substrate", rule_id
        assert block["B_role"] == (
            "inducer" if "INDUCTION" in candidate_type else "inhibitor"
        ), rule_id
        assert (
            block.get("id") if input_key == "enzyme_id" else block.get("family")
        ) == (target if input_key == "enzyme_id" else "ABCB1"), rule_id
        if input_key == "transporter_family":
            assert target == TRANSPORTER_PGP
