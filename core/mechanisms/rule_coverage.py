"""Explicit curated rule identities used for public summary reconciliation."""

from __future__ import annotations

from core.constants import TRANSPORTER_PGP, normalize_transporter_id
from core.enums import Domain
from core.mechanisms.candidates import (
    CANDIDATE_ENZYME_INDUCTION,
    CANDIDATE_ENZYME_INHIBITION,
    CANDIDATE_TRANSPORTER_INDUCTION,
    CANDIDATE_TRANSPORTER_INHIBITION,
)
from core.mechanisms.finding_identity import PDFindingIdentity, PKFindingIdentity
from core.models import PairReport, RuleHit

# Only single-mechanism exposure rules belong here. Composite and prodrug
# rules may describe a different outcome from the substrate exposure pattern.
CURATED_PK_RULES: dict[str, tuple[str, str, str]] = {
    "PK_CYP1A2_INHIB_SUBSTRATE": (CANDIDATE_ENZYME_INHIBITION, "CYP1A2", "enzyme_id"),
    "PK_CYP2D6_INHIB_SUBSTRATE": (CANDIDATE_ENZYME_INHIBITION, "CYP2D6", "enzyme_id"),
    "PK_CYP3A4_STRONG_INHIB": (CANDIDATE_ENZYME_INHIBITION, "CYP3A4", "enzyme_id"),
    "PK_UGT1A1_INHIB": (CANDIDATE_ENZYME_INHIBITION, "UGT1A1", "enzyme_id"),
    "PK_CYP3A4_STRONG_INDUC": (CANDIDATE_ENZYME_INDUCTION, "CYP3A4", "enzyme_id"),
    "PK_PGP_INHIB_DIGOXIN": (
        CANDIDATE_TRANSPORTER_INHIBITION,
        TRANSPORTER_PGP,
        "transporter_family",
    ),
    "PK_PGP_INDUC_DIGOXIN": (
        CANDIDATE_TRANSPORTER_INDUCTION,
        TRANSPORTER_PGP,
        "transporter_family",
    ),
}

# These definitions have a single pd_overlap effect in the curated rules.
# Drug-specific and composite rules are deliberately excluded.
CURATED_PD_RULES: dict[str, str] = {
    "PD_ACTIVATION_AGITATION_ADDITIVE": "activation_agitation_risk",
    "PD_ALPHA1_ANTAGONISM_ADDITIVE": "alpha1_antagonism",
    "PD_ANTICHOLINERGIC_EFFECTS_ADDITIVE": "anticholinergic_effects",
    "PD_BLEEDING_ADDITIVE": "bleeding",
    "PD_BRADYCARDIA_ADDITIVE": "bradycardia",
    "PD_CNS_DEP_ADDITIVE": "CNS_depression",
    "PD_CNS_DEPRESSION_ADDITIVE_HIGH": "CNS_depression",
    "PD_CNS_STIMULATION_ADDITIVE": "CNS_stimulation",
    "PD_CONSTIPATION_ADDITIVE_MEDIUM": "constipation_risk",
    "PD_D2_BLOCKADE_ADDITIVE": "D2_blockade",
    "PD_EPS_RISK_ADDITIVE": "EPS_risk",
    "PD_H1_ANTAGONISM_ADDITIVE": "h1_antagonism",
    "PD_HYPERKALEMIA_RISK_ADDITIVE": "hyperkalemia_risk",
    "PD_HYPOKALEMIA_RISK_ADDITIVE": "hypokalemia_risk",
    "PD_HYPERTENSION_ADDITIVE": "hypertension",
    "PD_INSOMNIA_ADDITIVE": "insomnia_risk",
    "PD_INTRACRANIAL_HYPERTENSION_RISK_ADDITIVE": "intracranial_hypertension_risk",
    "PD_LITHIUM_LEVEL_INCREASE_RISK": "lithium_level_increase_risk",
    "PD_MANIA_ACTIVATION_ADDITIVE": "mania_activation_risk",
    "PD_NAUSEA_ADDITIVE": "nausea",
    "PD_NEUROTOXICITY_RISK_ADDITIVE": "neurotoxicity_risk",
    "PD_NORADRENERGIC_EFFECTS_ADDITIVE": "noradrenergic_effects",
    "PD_OPIOID_ANTAGONIST_OVERLAP": "opioid_antagonist",
    "PD_ORTHOSTATIC_HYPOTENSION_ADDITIVE": "orthostatic_hypotension",
    "PD_PHOTOSENSITIVITY_RISK_ADDITIVE": "photosensitivity_risk",
    "PD_QT_ADDITIVE": "QT_prolongation",
    "PD_QT_PROLONGATION_ADDITIVE_HIGH": "QT_prolongation",
    "PD_RESPIRATORY_DEPRESSION_ADDITIVE": "respiratory_depression",
    "PD_SEDATION_ADDITIVE": "sedation",
    "PD_SEIZURE_RISK_ADDITIVE": "seizure_risk",
    "PD_SEROTONERGIC_ADDITIVE": "serotonergic",
    "PD_SEROTONIN_SYNDROME_ADDITIVE": "serotonin_syndrome",
    "PD_SYMPATHETIC_STIMULATION_ADDITIVE": "sympathetic_stimulation",
    "PD_TACHYCARDIA_ADDITIVE": "tachycardia",
    "PD_URINARY_RETENTION_RISK_ADDITIVE": "urinary_retention_risk",
    "PD_WITHDRAWAL_RISK_OVERLAP": "withdrawal_risk",
}


def _validated_drugs(report: PairReport, hit: RuleHit) -> tuple[str, str] | None:
    inputs = hit.inputs or {}
    object_drug, precipitant_drug = inputs.get("A"), inputs.get("B")
    if (
        not isinstance(object_drug, str)
        or not isinstance(precipitant_drug, str)
        or not object_drug
        or not precipitant_drug
        or object_drug == precipitant_drug
        or {object_drug, precipitant_drug} != {report.drug_1, report.drug_2}
    ):
        return None
    return object_drug, precipitant_drug


def pk_rule_identity(report: PairReport, hit: RuleHit) -> PKFindingIdentity | None:
    mechanism = CURATED_PK_RULES.get(hit.rule_id)
    drugs = _validated_drugs(report, hit)
    if mechanism is None or hit.domain != Domain.PK or drugs is None:
        return None
    candidate_type, target, input_key = mechanism
    inputs = hit.inputs or {}
    if input_key == "enzyme_id":
        if inputs.get("enzyme_id") != target:
            return None
    else:
        transporter_id = inputs.get("transporter_id")
        if inputs.get("transporter_family") != "ABCB1" or (
            transporter_id is not None
            and (
                not isinstance(transporter_id, str)
                or normalize_transporter_id(transporter_id) != target
            )
        ):
            return None
    return PKFindingIdentity(drugs[0], drugs[1], candidate_type, target)


def pd_rule_identity(report: PairReport, hit: RuleHit) -> PDFindingIdentity | None:
    effect_id = CURATED_PD_RULES.get(hit.rule_id)
    drugs = _validated_drugs(report, hit)
    if (
        effect_id is None
        or hit.domain != Domain.PD
        or drugs is None
        or (hit.inputs or {}).get("effect_id") != effect_id
    ):
        return None
    return PDFindingIdentity(frozenset(drugs), effect_id)
