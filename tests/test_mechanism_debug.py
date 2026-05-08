from core.mechanism_debug import (
    format_mechanism_effect,
    format_mechanism_effects,
)
from core.mechanism_effect import MechanismEffect
from core.mechanism_registry import (
    MECHANISM_ENZYME_INHIBITION,
    MECHANISM_PD_EFFECT,
)


def test_format_mechanism_effect_formats_pd_effect():
    effect = MechanismEffect(
        mechanism=MECHANISM_PD_EFFECT,
        source_drug="vortioxetine",
        effect_id="nausea",
    )

    assert format_mechanism_effect(effect) == (
        "vortioxetine: PD_EFFECT nausea"
    )


def test_format_mechanism_effect_formats_target_based_effect():
    effect = MechanismEffect(
        mechanism=MECHANISM_ENZYME_INHIBITION,
        source_drug="bupropion",
        target="CYP2D6",
    )

    assert format_mechanism_effect(effect) == (
        "bupropion: ENZYME_INHIBITION CYP2D6"
    )


def test_format_mechanism_effects_formats_multiple_effects():
    effects = [
        MechanismEffect(
            mechanism=MECHANISM_ENZYME_INHIBITION,
            source_drug="bupropion",
            target="CYP2D6",
        ),
        MechanismEffect(
            mechanism=MECHANISM_PD_EFFECT,
            source_drug="vortioxetine",
            effect_id="nausea",
        ),
    ]

    assert format_mechanism_effects(effects) == [
        "bupropion: ENZYME_INHIBITION CYP2D6",
        "vortioxetine: PD_EFFECT nausea",
    ]