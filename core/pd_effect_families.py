from __future__ import annotations

PD_EFFECT_RULE_FAMILIES = {
    "blood_pressure_increase": "hypertension",
    "hypertension_risk": "hypertension",
    "lithium_increase_risk": "lithium_level_increase_risk",
    "seizure_threshold": "seizure_risk",
    "sympathomimetic_activity": "sympathetic_stimulation",
    "tachycardia_risk": "tachycardia",
}


def canonical_pd_effect_family(effect_id: str) -> str:
    return PD_EFFECT_RULE_FAMILIES.get(effect_id, effect_id)


def pd_effects_share_family(left: str, right: str) -> bool:
    return canonical_pd_effect_family(left) == canonical_pd_effect_family(right)
