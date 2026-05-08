from core.mechanism_inference import infer_mechanism_effects_for_drugs
from core.mechanism_registry import (
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_SUBSTRATE,
    MECHANISM_PD_EFFECT,
    MECHANISM_TRANSPORTER_INHIBITION,
    MECHANISM_TRANSPORTER_SUBSTRATE,
)
from core.models import Drug, EnzymeRole, Facts, PDEffect, TransporterRole


def test_infer_mechanism_effects_for_bupropion_vortioxetine():
    facts = Facts(
        drugs={
            "bupropion": Drug(
                id="bupropion",
                generic_name="bupropion",
                drug_class="NDRI antidepressant",
                therapeutic_index="moderate",
            ),
            "vortioxetine": Drug(
                id="vortioxetine",
                generic_name="vortioxetine",
                drug_class="serotonin modulator and stimulator",
                therapeutic_index="moderate",
            ),
            "fluconazole": Drug(
                id="fluconazole",
                generic_name="fluconazole",
                drug_class="azole antifungal",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={
            "bupropion": [
                EnzymeRole(
                    enzyme_id="CYP2D6",
                    role="inhibitor",
                    strength="strong",
                )
            ],
            "vortioxetine": [
                EnzymeRole(
                    enzyme_id="CYP2D6",
                    role="substrate",
                    fraction_metabolized=0.6,
                ),
                EnzymeRole(
                    enzyme_id="CYP3A4",
                    role="substrate",
                    fraction_metabolized=0.2,
                ),
            ],
            "fluconazole": [
                EnzymeRole(
                    enzyme_id="CYP2C9",
                    role="inhibitor",
                    strength="moderate",
                )
            ],
        },
        transporter_roles={},
        pd_effects={
            "vortioxetine": [
                PDEffect(
                    effect_id="serotonergic",
                    direction="increase",
                    magnitude="moderate",
                ),
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="high",
                ),
            ],
            "fluconazole": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="moderate",
                )
            ],
        },
    )

    effects = infer_mechanism_effects_for_drugs(
        ["bupropion", "vortioxetine"],
        facts,
    )

    keys = {
        (effect.mechanism, effect.source_drug, effect.target, effect.effect_id)
        for effect in effects
    }

    assert (
        MECHANISM_ENZYME_INHIBITION,
        "bupropion",
        "CYP2D6",
        None,
    ) in keys
    assert (
        MECHANISM_ENZYME_SUBSTRATE,
        "vortioxetine",
        "CYP2D6",
        None,
    ) in keys
    assert (
        MECHANISM_ENZYME_SUBSTRATE,
        "vortioxetine",
        "CYP3A4",
        None,
    ) in keys
    assert (
        MECHANISM_PD_EFFECT,
        "vortioxetine",
        None,
        "serotonergic",
    ) in keys
    assert (
        MECHANISM_PD_EFFECT,
        "vortioxetine",
        None,
        "nausea",
    ) in keys

    assert all(effect.source_drug != "fluconazole" for effect in effects)


def test_infer_mechanism_effects_for_clarithromycin_digoxin():
    facts = Facts(
        drugs={
            "clarithromycin": Drug(
                id="clarithromycin",
                generic_name="clarithromycin",
                drug_class="macrolide antibiotic",
                therapeutic_index="moderate",
            ),
            "digoxin": Drug(
                id="digoxin",
                generic_name="digoxin",
                drug_class="cardiac glycoside",
                therapeutic_index="narrow",
            ),
        },
        enzyme_roles={
            "clarithromycin": [
                EnzymeRole(
                    enzyme_id="CYP3A4",
                    role="inhibitor",
                    strength="strong",
                )
            ],
        },
        transporter_roles={
            "clarithromycin": [
                TransporterRole(
                    transporter_id="P-gp",
                    role="inhibitor",
                    strength="strong",
                )
            ],
            "digoxin": [
                TransporterRole(
                    transporter_id="P-gp",
                    role="substrate",
                    strength="major",
                )
            ],
        },
        pd_effects={
            "clarithromycin": [
                PDEffect(
                    effect_id="QT_prolongation",
                    direction="increase",
                    magnitude="moderate",
                ),
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="moderate",
                ),
            ],
            "digoxin": [
                PDEffect(
                    effect_id="bradycardia",
                    direction="increase",
                    magnitude="high",
                )
            ],
        },
    )

    effects = infer_mechanism_effects_for_drugs(
        ["clarithromycin", "digoxin"],
        facts,
    )

    keys = {
        (effect.mechanism, effect.source_drug, effect.target, effect.effect_id)
        for effect in effects
    }

    assert (
        MECHANISM_ENZYME_INHIBITION,
        "clarithromycin",
        "CYP3A4",
        None,
    ) in keys
    assert (
        MECHANISM_TRANSPORTER_INHIBITION,
        "clarithromycin",
        "P-gp",
        None,
    ) in keys
    assert (
        MECHANISM_TRANSPORTER_SUBSTRATE,
        "digoxin",
        "P-gp",
        None,
    ) in keys
    assert (
        MECHANISM_PD_EFFECT,
        "clarithromycin",
        None,
        "QT_prolongation",
    ) in keys
    assert (
        MECHANISM_PD_EFFECT,
        "clarithromycin",
        None,
        "nausea",
    ) in keys
    assert (
        MECHANISM_PD_EFFECT,
        "digoxin",
        None,
        "bradycardia",
    ) in keys


def test_infer_mechanism_effects_returns_empty_for_unknown_selected_drug():
    facts = Facts(
        drugs={
            "bupropion": Drug(
                id="bupropion",
                generic_name="bupropion",
                drug_class="NDRI antidepressant",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={
            "bupropion": [
                EnzymeRole(
                    enzyme_id="CYP2D6",
                    role="inhibitor",
                    strength="strong",
                )
            ],
        },
        transporter_roles={},
        pd_effects={},
    )

    effects = infer_mechanism_effects_for_drugs(
        ["not_a_real_drug"],
        facts,
    )

    assert effects == []


def test_infer_mechanism_effects_dedupes_selected_effects():
    facts = Facts(
        drugs={
            "vortioxetine": Drug(
                id="vortioxetine",
                generic_name="vortioxetine",
                drug_class="serotonin modulator and stimulator",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={},
        transporter_roles={},
        pd_effects={
            "vortioxetine": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="high",
                ),
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="high",
                ),
            ],
        },
    )

    effects = infer_mechanism_effects_for_drugs(
        ["vortioxetine"],
        facts,
    )

    assert len(effects) == 1
    assert effects[0].mechanism == MECHANISM_PD_EFFECT
    assert effects[0].source_drug == "vortioxetine"
    assert effects[0].effect_id == "nausea"