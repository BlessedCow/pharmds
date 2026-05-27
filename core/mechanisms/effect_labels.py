from __future__ import annotations

PUBLIC_EFFECT_LABELS = {
    "QT_prolongation": "QT prolongation",
    "h1_antagonism": "antihistamine/sedation-related effect",
    "tachycardia_risk": "increased heart-rate risk",
    "hypertension_risk": "blood-pressure elevation risk",
    "intracranial_hypertension_risk": "intracranial hypertension risk",
    "CNS_depression": "CNS depression",
    "serotonin_syndrome": "serotonin syndrome",
    "seizure_risk": "seizure risk",
    "orthostatic_hypotension": "orthostatic hypotension",
    "anticholinergic_effects": "anticholinergic effects",
    "activation_agitation_risk": "activation/agitation risk",
    "insomnia_risk": "insomnia risk",
    "nausea": "nausea",
    "bleeding": "bleeding risk",
}


def effect_display_label(effect_id: str | None) -> str:
    if not effect_id:
        return "unspecified effect"

    return PUBLIC_EFFECT_LABELS.get(effect_id, effect_id.replace("_", " "))