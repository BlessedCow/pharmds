import json
from pathlib import Path

import pytest

from core.mechanisms.effects import (
    MechanismEffect,
    dedupe_mechanism_effects,
    drug_to_mechanism_effects,
    facts_to_mechanism_effects,
)
from core.mechanisms.registry import (
    MECHANISM_ENZYME_INDUCTION,
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_ENZYME_SUBSTRATE,
    MECHANISM_PD_EFFECT,
    MECHANISM_TRANSPORTER_INDUCTION,
    MECHANISM_TRANSPORTER_INHIBITION,
    MECHANISM_TRANSPORTER_SUBSTRATE,
    validate_pd_effect,
)
from core.models import Drug, EnzymeRole, Facts, PDEffect

CURATION_PATH = Path("data/curation/drugs.json")


def _curated_drug(drug_id: str) -> dict:
    data = json.loads(CURATION_PATH.read_text(encoding="utf-8"))
    for drug in data["drugs"]:
        if drug["id"] == drug_id:
            return drug
    raise AssertionError(f"Missing curated drug: {drug_id}")


def test_pd_effect_requires_effect_id():
    with pytest.raises(ValueError, match="PD_EFFECT requires effect_id"):
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="vortioxetine",
        )


def test_non_pd_mechanism_requires_target():
    with pytest.raises(ValueError, match="requires target"):
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_INHIBITION,
            source_drug="bupropion",
        )


def test_unknown_mechanism_rejected():
    with pytest.raises(ValueError, match="Unknown mechanism"):
        MechanismEffect(
            mechanism="MAJOR_INTERACTION",
            source_drug="bupropion",
            target="CYP2D6",
        )


def test_unknown_pd_effect_rejected():
    with pytest.raises(ValueError, match="Unknown PD effect"):
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="example_drug",
            effect_id="made_up_effect",
        )


def test_validate_pd_effect_normalizes_existing_alias_case():
    assert validate_pd_effect("H1_antagonism") == "h1_antagonism"


def test_drug_to_mechanism_effects_maps_curated_clarithromycin():
    effects = drug_to_mechanism_effects(
        "clarithromycin",
        _curated_drug("clarithromycin"),
    )

    keys = {(effect.mechanism, effect.target, effect.effect_id) for effect in effects}

    assert (MECHANISM_ENZYME_INHIBITION, "CYP3A4", None) in keys
    assert (MECHANISM_TRANSPORTER_INHIBITION, "P-gp", None) in keys
    assert (MECHANISM_PD_EFFECT, None, "QT_prolongation") in keys
    assert (MECHANISM_PD_EFFECT, None, "nausea") in keys


def test_drug_to_mechanism_effects_maps_curated_rifampin_induction():
    effects = drug_to_mechanism_effects("rifampin", _curated_drug("rifampin"))

    keys = {(effect.mechanism, effect.target, effect.effect_id) for effect in effects}

    assert (MECHANISM_ENZYME_INDUCTION, "CYP3A4", None) in keys
    assert (MECHANISM_TRANSPORTER_INDUCTION, "P-gp", None) in keys


def test_drug_to_mechanism_effects_maps_curated_digoxin_substrate():
    effects = drug_to_mechanism_effects("digoxin", _curated_drug("digoxin"))

    keys = {(effect.mechanism, effect.target, effect.effect_id) for effect in effects}

    assert (MECHANISM_TRANSPORTER_SUBSTRATE, "P-gp", None) in keys
    assert (MECHANISM_PD_EFFECT, None, "bradycardia") in keys


def test_drug_to_mechanism_effects_maps_curated_vortioxetine_substrates_and_pd():
    effects = drug_to_mechanism_effects(
        "vortioxetine",
        _curated_drug("vortioxetine"),
    )

    keys = {(effect.mechanism, effect.target, effect.effect_id) for effect in effects}

    assert (MECHANISM_ENZYME_SUBSTRATE, "CYP2D6", None) in keys
    assert (MECHANISM_ENZYME_SUBSTRATE, "CYP3A4", None) in keys
    assert (MECHANISM_PD_EFFECT, None, "serotonergic") in keys
    assert (MECHANISM_PD_EFFECT, None, "nausea") in keys


def test_facts_to_mechanism_effects_uses_existing_facts_model():
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
                )
            ],
        },
        transporter_roles={},
        pd_effects={
            "vortioxetine": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="high",
                )
            ]
        },
    )

    effects = facts_to_mechanism_effects(facts)
    keys = {
        (effect.mechanism, effect.source_drug, effect.target, effect.effect_id)
        for effect in effects
    }

    assert (MECHANISM_ENZYME_INHIBITION, "bupropion", "CYP2D6", None) in keys
    assert (MECHANISM_ENZYME_SUBSTRATE, "vortioxetine", "CYP2D6", None) in keys
    assert (MECHANISM_PD_EFFECT, "vortioxetine", None, "nausea") in keys


def test_dedupe_mechanism_effects_preserves_first_seen_order():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="vortioxetine",
            effect_id="nausea",
        ),
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="vortioxetine",
            effect_id="nausea",
        ),
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="fluconazole",
            effect_id="nausea",
        ),
    ]

    deduped = dedupe_mechanism_effects(effects)

    assert len(deduped) == 2
    assert deduped[0].source_drug == "vortioxetine"
    assert deduped[1].source_drug == "fluconazole"
