"""
from __future__ import annotations

from app.cli import DB_PATH, connect, load_facts


VALID_DIRECTIONS = {"increase", "decrease"}
VALID_MAGNITUDES = {"low", "medium", "high"}

KNOWN_PD_EFFECT_IDS = {
    "CNS_depression",
    "QT_prolongation",
    "bleeding",
    "bradycardia",
    "serotonergic",
    "serotonin_syndrome",
    "respiratory_depression",
    "sedation",
    "h1_antagonism",
    "seizure_risk",
    "opioid_antagonist",
    "withdrawal_risk",
    "neurotoxicity_risk",
    "seizure_threshold",
    "hypokalemia_risk",
    "hyperkalemia_risk",
    "renal_function",
    "lithium_increase_risk",
    "orthostatic_hypotension",
    "anticholinergic_effects",
    "noradrenergic_effects",
    "alpha1_antagonism",
    "D2_blockade",
    "EPS_risk",
    "hypersensitivity_risk",
    "sympathomimetic_activity",
    "blood_pressure_increase",
    "tachycardia_risk",
    "hypertension_risk",
    "photosensitivity_risk",
    "intracranial_hypertension_risk",
    "urinary_retention_risk",
    "constipation_risk",
    "mania_activation_risk",
    "insomnia_risk",
    "activation_agitation_risk",
}


def test_all_pd_effect_entries_are_valid():
    conn = connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM drugs")
    drug_ids = [row[0] for row in cur.fetchall()]

    facts = load_facts(conn, drug_ids, patient_flags={})

    for drug_id in drug_ids:
        drug_facts = facts.get(drug_id, {})
        for effect in drug_facts.get("pd_effects", []):
            assert effect["effect_id"] in KNOWN_PD_EFFECT_IDS, (
                f"{drug_id} has unknown pd effect id: {effect['effect_id']}"
            )
            assert effect["direction"] in VALID_DIRECTIONS, (
                f"{drug_id} has invalid pd direction: {effect['direction']}"
            )
            assert effect["magnitude"] in VALID_MAGNITUDES, (
                f"{drug_id} has invalid pd magnitude: {effect['magnitude']}"
            )
            
def _pd_effect_ids_for(drug_id: str) -> set[str]:
    conn = connect(DB_PATH)
    facts = load_facts(conn, [drug_id], patient_flags={})
    return {e["effect_id"] for e in facts[drug_id].get("pd_effects", [])}


def test_methylphenidate_has_new_pd_effects():
    effect_ids = _pd_effect_ids_for("methylphenidate")
    assert "activation_agitation_risk" in effect_ids
    assert "insomnia_risk" in effect_ids
    assert "mania_activation_risk" in effect_ids


def test_vilazodone_has_new_pd_effects():
    effect_ids = _pd_effect_ids_for("vilazodone")
    assert "activation_agitation_risk" in effect_ids
    assert "insomnia_risk" in effect_ids
    assert "mania_activation_risk" in effect_ids


def test_varenicline_has_expected_new_pd_effects():
    effect_ids = _pd_effect_ids_for("varenicline")
    assert "activation_agitation_risk" in effect_ids
    assert "insomnia_risk" in effect_ids
    assert "mania_activation_risk" not in effect_ids
"""