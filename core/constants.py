from __future__ import annotations

# Canonical transporter IDs (internal representation)
TRANSPORTER_PGP = "P-gp"  # P-glycoprotein
TRANSPORTER_BCRP = "BCRP"
TRANSPORTER_OATP1B1 = "OATP1B1"
TRANSPORTER_SERT = "SERT"
TRANSPORTER_NET = "NET"

_TRANSPORTER_ALIASES: dict[str, str] = {
    # P-gp (ABCB1 / MDR1)
    "p-gp": TRANSPORTER_PGP,
    "pgp": TRANSPORTER_PGP,
    "p gp": TRANSPORTER_PGP,
    "p-glycoprotein": TRANSPORTER_PGP,
    "p glycoprotein": TRANSPORTER_PGP,
    "abcb1": TRANSPORTER_PGP,
    "mdr1": TRANSPORTER_PGP,
    # BCRP (ABCG2)
    "bcrp": TRANSPORTER_BCRP,
    "abcg2": TRANSPORTER_BCRP,
    # OATP1B1 (SLCO1B1)
    "oatp1b1": TRANSPORTER_OATP1B1,
    "slco1b1": TRANSPORTER_OATP1B1,
    # SERT (SLC6A4)
    "sert": TRANSPORTER_SERT,
    "slc6a4": TRANSPORTER_SERT,
    # NET (SLC6A2)
    "net": TRANSPORTER_NET,
    "slc6a2": TRANSPORTER_NET,
}


def normalize_transporter_id(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return _TRANSPORTER_ALIASES.get(s.lower(), s)

# Canonical PD effect IDs (internal representation)
PD_EFFECT_CNS_DEP = "CNS_depression"
PD_EFFECT_QT = "QT_prolongation"
PD_EFFECT_BLEEDING = "bleeding"
PD_EFFECT_BRADYCARDIA = "bradycardia"
PD_EFFECT_SEROTONERGIC = "serotonergic"
PD_EFFECT_SEROTONIN_SYNDROME = "serotonin_syndrome"

# Additional PD effects used for richer educational tagging
PD_EFFECT_RESP_DEP = "respiratory_depression"
PD_EFFECT_SEDATION = "sedation"
PD_EFFECT_H1_ANTAGONISM = "h1_antagonism"
PD_EFFECT_SEIZURE_RISK = "seizure_risk"
PD_EFFECT_OPIOID_ANTAGONIST = "opioid_antagonist"
PD_EFFECT_WITHDRAWAL = "withdrawal_risk"
PD_EFFECT_NEUROTOXICITY_RISK = "neurotoxicity_risk"
PD_EFFECT_SEIZURE_THRESHOLD = "seizure_threshold"
PD_EFFECT_HYPOKALEMIA = "hypokalemia_risk"
PD_EFFECT_HYPERKALEMIA = "hyperkalemia_risk"
PD_EFFECT_RENAL_FUNCTION = "renal_function"
PD_EFFECT_LITHIUM_INCREASE_RISK = "lithium_increase_risk"
PD_EFFECT_ORTHOSTATIC_HYPOTENSION = "orthostatic_hypotension"
PD_EFFECT_ANTICHOLINERGIC = "anticholinergic_effects"
PD_EFFECT_NORADRENERGIC = "noradrenergic_effects"
PD_EFFECT_ALPHA1_ANTAGONISM = "alpha1_antagonism"
PD_EFFECT_D2_BLOCKADE = "D2_blockade"
PD_EFFECT_EPS_RISK = "EPS_risk"
PD_EFFECT_HYPERSENSITIVITY_RISK = "hypersensitivity_risk"
PD_EFFECT_SYMPATHOMIMETIC = "sympathomimetic_activity"
PD_EFFECT_BP_INCREASE = "blood_pressure_increase"
PD_EFFECT_TACHYCARDIA_RISK = "tachycardia_risk"
PD_EFFECT_HYPERTENSION_RISK = "hypertension_risk"
PD_EFFECT_PHOTOSENSITIVITY_RISK = "photosensitivity_risk"
PD_EFFECT_INTRACRANIAL_HTN_RISK = "intracranial_hypertension_risk"
PD_EFFECT_URINARY_RETENTION_RISK = "urinary_retention_risk"
PD_EFFECT_CONSTIPATION_RISK = "constipation_risk"
PD_EFFECT_MANIA_ACTIVATION_RISK = "mania_activation_risk"
PD_EFFECT_INSOMNIA_RISK = "insomnia_risk"
PD_EFFECT_ACTIVATION_AGITATION_RISK = "activation_agitation_risk"

_PD_EFFECT_ALIASES: dict[str, str] = {
    # core
    "cns depression": PD_EFFECT_CNS_DEP,
    "cns_depression": PD_EFFECT_CNS_DEP,
    "qt": PD_EFFECT_QT,
    "qt prolongation": PD_EFFECT_QT,
    "qt_prolongation": PD_EFFECT_QT,
    "bleed": PD_EFFECT_BLEEDING,
    "bleeding": PD_EFFECT_BLEEDING,
    "brady": PD_EFFECT_BRADYCARDIA,
    "bradycardia": PD_EFFECT_BRADYCARDIA,
    
    # serotonergic effects
    "serotonergic": PD_EFFECT_SEROTONERGIC,
    "serotonin syndrome": PD_EFFECT_SEROTONIN_SYNDROME,
    "serotonin_syndrome": PD_EFFECT_SEROTONIN_SYNDROME,
    "serotonin_activity": PD_EFFECT_SEROTONERGIC,
    "serotonergic_activity": PD_EFFECT_SEROTONERGIC,
    
    # respiratory depression
    "resp depression": PD_EFFECT_RESP_DEP,
    "respiratory depression": PD_EFFECT_RESP_DEP,
    "respiratory_depression": PD_EFFECT_RESP_DEP,

    # sedation
    "sedation": PD_EFFECT_SEDATION,
    "sedating": PD_EFFECT_SEDATION,

    # H1 antagonism
    "h1 antagonism": PD_EFFECT_H1_ANTAGONISM,
    "h1_antagonism": PD_EFFECT_H1_ANTAGONISM,
    "h1 receptor antagonism": PD_EFFECT_H1_ANTAGONISM,
    "histamine h1 antagonism": PD_EFFECT_H1_ANTAGONISM,
    "histamine h1 blockade": PD_EFFECT_H1_ANTAGONISM,
    "h1 blockade": PD_EFFECT_H1_ANTAGONISM,
    "antihistamine": PD_EFFECT_H1_ANTAGONISM,
    
    # alpha-1 adrenergic antagonism
    "alpha1 antagonism":           PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha1_antagonism":           PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha-1 antagonism":          PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha1 blockade":             PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha-1 blockade":            PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha1 receptor antagonism":  PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha-1 receptor antagonism": PD_EFFECT_ALPHA1_ANTAGONISM,
    "alpha adrenergic blockade":   PD_EFFECT_ALPHA1_ANTAGONISM,
    
    # seizure risk / threshold lowering
    "seizure": PD_EFFECT_SEIZURE_RISK,
    "seizure risk": PD_EFFECT_SEIZURE_RISK,
    "seizure threshold": PD_EFFECT_SEIZURE_THRESHOLD,
    "seizure_threshold_lowering": PD_EFFECT_SEIZURE_THRESHOLD,
    "seizure_risk": PD_EFFECT_SEIZURE_RISK,

    # opioid antagonist
    "opioid antagonist": PD_EFFECT_OPIOID_ANTAGONIST,
    "opioid_antagonist": PD_EFFECT_OPIOID_ANTAGONIST,

    # withdrawal risk
    "withdrawal": PD_EFFECT_WITHDRAWAL,
    "withdrawal risk": PD_EFFECT_WITHDRAWAL,
    "precipitated withdrawal": PD_EFFECT_WITHDRAWAL,
    "precipitated_withdrawal": PD_EFFECT_WITHDRAWAL,
    "withdrawal_risk": PD_EFFECT_WITHDRAWAL,
    
    # potassium effects
    "hypokalemia_risk": PD_EFFECT_HYPOKALEMIA,
    "hypokalemia": PD_EFFECT_HYPOKALEMIA,
    "hyperkalemia_risk": PD_EFFECT_HYPERKALEMIA,
    "hyperkalemia": PD_EFFECT_HYPERKALEMIA,

    # renal function
    "renal function": PD_EFFECT_RENAL_FUNCTION,
    "renal_function": PD_EFFECT_RENAL_FUNCTION,
    
    # neurotoxicity risk
    "neurotoxicity": PD_EFFECT_NEUROTOXICITY_RISK,
    "neurotoxicity risk": PD_EFFECT_NEUROTOXICITY_RISK,
    "neurotoxicity_risk": PD_EFFECT_NEUROTOXICITY_RISK,
    
    # lithium effects
    "lithium increase risk": PD_EFFECT_LITHIUM_INCREASE_RISK,
    "lithium_increase_risk": PD_EFFECT_LITHIUM_INCREASE_RISK,
    "lithium increase": PD_EFFECT_LITHIUM_INCREASE_RISK,
    "lithium_increase": PD_EFFECT_LITHIUM_INCREASE_RISK, 

    # orthostatic hypotension
    "orthostatic hypotension": PD_EFFECT_ORTHOSTATIC_HYPOTENSION,
    "orthostatic_hypotension": PD_EFFECT_ORTHOSTATIC_HYPOTENSION,

    # anticholinergic effects
    "anticholinergic effects": PD_EFFECT_ANTICHOLINERGIC,
    "anticholinergic_effect": PD_EFFECT_ANTICHOLINERGIC,
    "anticholinergic_effects": PD_EFFECT_ANTICHOLINERGIC,

    # noradrenergic effects
    "noradrenergic effects": PD_EFFECT_NORADRENERGIC,
    "noradrenergic_effects": PD_EFFECT_NORADRENERGIC,
    
    # D2 blockade
    "d2 blockade": PD_EFFECT_D2_BLOCKADE,
    "d2_blockade": PD_EFFECT_D2_BLOCKADE,
    "dopamine d2 blockade": PD_EFFECT_D2_BLOCKADE,
    "dopamine_d2_blockade": PD_EFFECT_D2_BLOCKADE,

    # EPS risk
    "eps risk": PD_EFFECT_EPS_RISK,
    "eps_risk": PD_EFFECT_EPS_RISK,
    "extrapyramidal symptoms": PD_EFFECT_EPS_RISK,
    "extrapyramidal_symptoms": PD_EFFECT_EPS_RISK,
    "extrapyramidal symptom risk": PD_EFFECT_EPS_RISK,
    
    # hypersensitivity risk
    "hypersensitivity": PD_EFFECT_HYPERSENSITIVITY_RISK,
    "hypersensitivity risk": PD_EFFECT_HYPERSENSITIVITY_RISK,
    "hypersensitivity_risk": PD_EFFECT_HYPERSENSITIVITY_RISK,

    # sympathomimetic activity
    "sympathomimetic": PD_EFFECT_SYMPATHOMIMETIC,
    "sympathomimetic activity": PD_EFFECT_SYMPATHOMIMETIC,
    "sympathomimetic_activity": PD_EFFECT_SYMPATHOMIMETIC,

    # blood pressure increase
    "blood pressure increase": PD_EFFECT_BP_INCREASE,
    "blood_pressure_increase": PD_EFFECT_BP_INCREASE,
    "increased blood pressure": PD_EFFECT_BP_INCREASE,

    # tachycardia risk
    "tachycardia": PD_EFFECT_TACHYCARDIA_RISK,
    "tachycardia risk": PD_EFFECT_TACHYCARDIA_RISK,
    "tachycardia_risk": PD_EFFECT_TACHYCARDIA_RISK,

    # hypertension risk
    "hypertension": PD_EFFECT_HYPERTENSION_RISK,
    "hypertension risk": PD_EFFECT_HYPERTENSION_RISK,
    "hypertension_risk": PD_EFFECT_HYPERTENSION_RISK,

    # photosensitivity risk
    "photosensitivity": PD_EFFECT_PHOTOSENSITIVITY_RISK,
    "photosensitivity risk": PD_EFFECT_PHOTOSENSITIVITY_RISK,
    "photosensitivity_risk": PD_EFFECT_PHOTOSENSITIVITY_RISK,

    # intracranial hypertension risk
    "intracranial hypertension": PD_EFFECT_INTRACRANIAL_HTN_RISK,
    "intracranial hypertension risk": PD_EFFECT_INTRACRANIAL_HTN_RISK,
    "intracranial_hypertension_risk": PD_EFFECT_INTRACRANIAL_HTN_RISK,

    # urinary retention risk
    "urinary retention": PD_EFFECT_URINARY_RETENTION_RISK,
    "urinary retention risk": PD_EFFECT_URINARY_RETENTION_RISK,
    "urinary_retention_risk": PD_EFFECT_URINARY_RETENTION_RISK,

    # constipation risk
    "constipation": PD_EFFECT_CONSTIPATION_RISK,
    "constipation risk": PD_EFFECT_CONSTIPATION_RISK,
    "constipation_risk": PD_EFFECT_CONSTIPATION_RISK,
    
        # mania / activation risk
    "mania activation risk": PD_EFFECT_MANIA_ACTIVATION_RISK,
    "mania_activation_risk": PD_EFFECT_MANIA_ACTIVATION_RISK,
    "mania risk": PD_EFFECT_MANIA_ACTIVATION_RISK,

    # insomnia risk
    "insomnia": PD_EFFECT_INSOMNIA_RISK,
    "insomnia risk": PD_EFFECT_INSOMNIA_RISK,
    "insomnia_risk": PD_EFFECT_INSOMNIA_RISK,
    "sleep disturbance": PD_EFFECT_INSOMNIA_RISK,

    # activation / agitation risk
    "activation agitation risk": PD_EFFECT_ACTIVATION_AGITATION_RISK,
    "activation_agitation_risk": PD_EFFECT_ACTIVATION_AGITATION_RISK,
    "activation/agitation risk": PD_EFFECT_ACTIVATION_AGITATION_RISK,
    "agitation risk": PD_EFFECT_ACTIVATION_AGITATION_RISK,
    "activation": PD_EFFECT_ACTIVATION_AGITATION_RISK,
    "agitation": PD_EFFECT_ACTIVATION_AGITATION_RISK,
    
}


def normalize_pd_effect_id(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return _PD_EFFECT_ALIASES.get(s.lower(), s)
