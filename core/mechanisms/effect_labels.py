from __future__ import annotations

from core import constants as core_constants

# Public narrative labels are intentionally sentence friendly.
# Do not titlecase these because they are embedded inside summaries.
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


# UI labels are separate because these appear as standalone options
# in the frontend rather than inside prose.
PD_EFFECT_OPTION_LABELS = {
    "CNS_depression": "CNS Depression",
    "QT_prolongation": "QT Prolongation",
    "bleeding": "Bleeding Risk",
    "bradycardia": "Bradycardia",
    "serotonergic": "Serotonergic Effects",
    "serotonin_syndrome": "Serotonin Syndrome",
    "nausea": "Nausea",
    "respiratory_depression": "Respiratory Depression",
    "sedation": "Sedation",
    "h1_antagonism": "H1 Antagonism",
    "seizure_risk": "Seizure Risk",
    "opioid_antagonist": "Opioid Antagonism",
    "withdrawal_risk": "Withdrawal Risk",
    "neurotoxicity_risk": "Neurotoxicity Risk",
    "seizure_threshold": "Seizure Threshold",
    "hypokalemia_risk": "Hypokalemia Risk",
    "hyperkalemia_risk": "Hyperkalemia Risk",
    "renal_function": "Renal Function",
    "lithium_increase_risk": "Lithium Increase Risk",
    "orthostatic_hypotension": "Orthostatic Hypotension",
    "anticholinergic_effects": "Anticholinergic Effects",
    "noradrenergic_effects": "Noradrenergic Effects",
    "alpha1_antagonism": "Alpha-1 Antagonism",
    "D2_blockade": "D2 Blockade",
    "EPS_risk": "EPS Risk",
    "hypersensitivity_risk": "Hypersensitivity Risk",
    "sympathomimetic_activity": "Sympathomimetic Activity",
    "blood_pressure_increase": "Blood Pressure Increase",
    "tachycardia_risk": "Tachycardia Risk",
    "hypertension_risk": "Hypertension Risk",
    "photosensitivity_risk": "Photosensitivity Risk",
    "intracranial_hypertension_risk": (
        "Intracranial Hypertension Risk"
    ),
    "urinary_retention_risk": "Urinary Retention Risk",
    "constipation_risk": "Constipation Risk",
    "mania_activation_risk": "Mania Activation Risk",
    "insomnia_risk": "Insomnia Risk",
    "activation_agitation_risk": "Activation / Agitation Risk",
    "nAChR_antagonism": "nAChR Antagonism",
    "cholinergic_modulation": "Cholinergic Modulation",
}


def effect_display_label(effect_id: str | None) -> str:
    if not effect_id:
        return "unspecified effect"

    return PUBLIC_EFFECT_LABELS.get(
        effect_id,
        effect_id.replace("_", " "),
    )


def pd_effect_option_label(effect_id: str) -> str:
    return PD_EFFECT_OPTION_LABELS.get(
        effect_id,
        effect_id.replace("_", " "),
    )


def _canonical_pd_effect_ids() -> tuple[str, ...]:
    effect_ids = {
        value
        for name, value in vars(core_constants).items()
        if name.startswith("PD_EFFECT_")
        and isinstance(value, str)
    }

    return tuple(
        sorted(
            effect_ids,
            key=lambda effect_id: (
                pd_effect_option_label(effect_id).lower(),
                effect_id,
            ),
        )
    )


PD_EFFECT_FILTER_IDS = _canonical_pd_effect_ids()

SUPPORTED_PD_EFFECT_IDS = frozenset(PD_EFFECT_FILTER_IDS)


def pd_effect_options() -> tuple[tuple[str, str], ...]:
    return tuple(
        (
            effect_id,
            pd_effect_option_label(effect_id),
        )
        for effect_id in PD_EFFECT_FILTER_IDS
    )