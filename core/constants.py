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
    "serotonergic": PD_EFFECT_SEROTONERGIC,
    "serotonin syndrome": PD_EFFECT_SEROTONIN_SYNDROME,
    "serotonin_syndrome": PD_EFFECT_SEROTONIN_SYNDROME,
    "serotonin_activity": PD_EFFECT_SEROTONERGIC,
    
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
    "H1_antagonism": PD_EFFECT_H1_ANTAGONISM,
    "H1 antagonist": PD_EFFECT_H1_ANTAGONISM,
    "h1 receptor antagonism": PD_EFFECT_H1_ANTAGONISM,
    "histamine h1 antagonism": PD_EFFECT_H1_ANTAGONISM,
    "histamine h1 blockade": PD_EFFECT_H1_ANTAGONISM,
    "h1 blockace": PD_EFFECT_H1_ANTAGONISM,
    "antihistamine": PD_EFFECT_H1_ANTAGONISM,
    
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

    # noradrenergic effects
    "noradrenergic effects": PD_EFFECT_NORADRENERGIC
}


def normalize_pd_effect_id(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return _PD_EFFECT_ALIASES.get(s.lower(), s)
