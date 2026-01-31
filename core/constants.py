from __future__ import annotations
from typing import Dict

# Canonical transporter IDs (internal representation)

TRANSPORTER_PGP = "P-gp"  # P-glycoprotein
TRANSPORTER_BCRP = "BCRP"
TRANSPORTER_OATP1B1 = "OATP1B1"

_TRANSPORTER_ALIASES: Dict[str, str] = {
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


_PD_EFFECT_ALIASES: Dict[str, str] = {
    "cns depression": PD_EFFECT_CNS_DEP,
    "cns_depression": PD_EFFECT_CNS_DEP,
    "qt": PD_EFFECT_QT,
    "qt prolongation": PD_EFFECT_QT,
    "qt_prolongation": PD_EFFECT_QT,
    "bleed": PD_EFFECT_BLEEDING,
    "brady": PD_EFFECT_BRADYCARDIA,
    "serotonin syndrome": PD_EFFECT_SEROTONIN_SYNDROME,
    "serotonin_syndrome": PD_EFFECT_SEROTONIN_SYNDROME,
}


def normalize_pd_effect_id(raw: str) -> str:
    if raw is None:
        return ""
    s = str(raw).strip()
    if not s:
        return ""
    return _PD_EFFECT_ALIASES.get(s.lower(), s)