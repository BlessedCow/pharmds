from __future__ import annotations

# Canonical transporter IDs (internal representation)

TRANSPORTER_PGP = "P-gp"  # P-glycoprotein
TRANSPORTER_BCRP = "BCRP"
TRANSPORTER_OATP1B1 = "OATP1B1"

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
PD_EFFECT_SEIZURE_RISK = "seizure_risk"
PD_EFFECT_OPIOID_ANTAGONIST = "opioid_antagonist"
PD_EFFECT_WITHDRAWAL = "withdrawal_risk"




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

    # respiratory depression
    "resp depression": PD_EFFECT_RESP_DEP,
    "respiratory depression": PD_EFFECT_RESP_DEP,
    "respiratory_depression": PD_EFFECT_RESP_DEP,

    # sedation
    "sedation": PD_EFFECT_SEDATION,
    "sedating": PD_EFFECT_SEDATION,

    # seizure risk / threshold lowering
    "seizure": PD_EFFECT_SEIZURE_RISK,
    "seizure risk": PD_EFFECT_SEIZURE_RISK,
    "seizure threshold": PD_EFFECT_SEIZURE_RISK,
    "seizure_threshold_lowering": PD_EFFECT_SEIZURE_RISK,
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
}


def normalize_pd_effect_id(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return _PD_EFFECT_ALIASES.get(s.lower(), s)
