from __future__ import annotations

import json
from pathlib import Path

RULE_DIR = Path("rules/rule_defs")

EXPECTED_PK_RULE_IDS = {
    "PK_BCRP_INHIB_SUBSTRATE",
    "PK_CYP1A2_INHIB_SUBSTRATE",
    "PK_CYP1A2_INHIB_TIZANIDINE",
    "PK_CYP2C19_INHIB_CLOPIDOGREL",
    "PK_CYP2C9_INHIB_WARFARIN",
    "PK_CYP2D6_INHIB_SUBSTRATE",
    "PK_CYP2D6_INHIB_TRAMADOL",
    "PK_CYP3A4_STRONG_INDUC",
    "PK_CYP3A4_STRONG_INHIB",
    "PK_DOXYCYCLINE_AMOXICILLIN",
    "PK_DOXYCYCLINE_CALCIUM_CARBONATE",
    "PK_DOXYCYCLINE_WARFARIN",
    "PK_LISDEXAMFETAMINE_FLUOXETINE",
    "PK_METHADONE_CARBAMAZEPINE",
    "PK_METHADONE_FLUOXETINE",
    "PK_OATP_INHIB",
    "PK_PGP_INDUC_DIGOXIN",
    "PK_PGP_INHIB_DIGOXIN",
    "PK_UGT1A1_INHIB",
    "PK_VIBEGRON_DIGOXIN",
}

EXPECTED_PD_EFFECT_IDS = {
    "activation_agitation_risk",
    "alpha1_antagonism",
    "bleeding",
    "bradycardia",
    "CNS_depression",
    "CNS_stimulation",
    "constipation_risk",
    "D2_blockade",
    "EPS_risk",
    "h1_antagonism",
    "hypertension",
    "insomnia_risk",
    "lithium_level_increase_risk",
    "mania_activation_risk",
    "nausea",
    "opioid_antagonist",
    "QT_prolongation",
    "respiratory_depression",
    "sedation",
    "seizure_risk",
    "serotonergic",
    "serotonin_syndrome",
    "sympathetic_stimulation",
    "tachycardia",
    "withdrawal_risk",
}

EXPECTED_EXPLICIT_PK_PAIR_RULE_IDS = {
    "PK_DOXYCYCLINE_AMOXICILLIN",
    "PK_DOXYCYCLINE_CALCIUM_CARBONATE",
    "PK_DOXYCYCLINE_WARFARIN",
    "PK_LISDEXAMFETAMINE_FLUOXETINE",
    "PK_METHADONE_CARBAMAZEPINE",
    "PK_METHADONE_FLUOXETINE",
    "PK_VIBEGRON_DIGOXIN",
}


def _load_rule_defs() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(RULE_DIR.glob("*.json"))
    ]


def test_pairwise_pk_rule_inventory_is_documented() -> None:
    rules = _load_rule_defs()

    pk_rule_ids = {rule["id"] for rule in rules if rule["domain"] == "PK"}
    explicit_pk_pair_rule_ids = {
        rule["id"]
        for rule in rules
        if rule["domain"] == "PK" and "drug_pair" in rule.get("logic", {})
    }

    assert pk_rule_ids == EXPECTED_PK_RULE_IDS
    assert explicit_pk_pair_rule_ids == EXPECTED_EXPLICIT_PK_PAIR_RULE_IDS


def test_pairwise_pd_overlap_inventory_is_documented() -> None:
    rules = _load_rule_defs()

    pd_rules = [rule for rule in rules if rule["domain"] == "PD"]
    pd_effect_ids = {
        rule["logic"]["pd_overlap"]["effect_id"]
        for rule in pd_rules
        if "pd_overlap" in rule.get("logic", {})
    }

    assert len(pd_rules) == 27
    assert all("pd_overlap" in rule.get("logic", {}) for rule in pd_rules)
    assert pd_effect_ids == EXPECTED_PD_EFFECT_IDS


def test_pairwise_rule_inventory_has_migration_relevant_constraints() -> None:
    rules = _load_rule_defs()
    logic_blocks = [rule.get("logic", {}) for rule in rules]

    assert any("A_ti" in logic for logic in logic_blocks)
    assert any("A_name_is" in logic for logic in logic_blocks)
    assert any("A_name_not_is" in logic for logic in logic_blocks)
    assert any(
        "B_strength_in" in logic.get("enzyme", {})
        or "B_strength_in" in logic.get("transporter", {})
        for logic in logic_blocks
    )