from core.evidence.gating import (
    filter_facts_to_evidence_backed_pd_effects,
    filter_pd_effects_to_evidence_backed,
    is_pd_effect_evidence_backed,
)
from core.models import Drug, EnzymeRole, Facts, PDEffect, TransporterRole


def test_is_pd_effect_evidence_backed_returns_true_for_approved_active_claim():
    effect = PDEffect(
        effect_id="nausea",
        direction="increase",
        magnitude="medium",
    )

    assert is_pd_effect_evidence_backed("clarithromycin", effect) is True


def test_is_pd_effect_evidence_backed_returns_false_for_missing_claim():
    effect = PDEffect(
        effect_id="not_real_effect",
        direction="increase",
        magnitude="medium",
    )

    assert is_pd_effect_evidence_backed("clarithromycin", effect) is False


def test_filter_pd_effects_to_evidence_backed_keeps_supported_effects():
    effects = [
        PDEffect(
            effect_id="nausea",
            direction="increase",
            magnitude="medium",
        ),
        PDEffect(
            effect_id="not_real_effect",
            direction="increase",
            magnitude="medium",
        ),
    ]

    filtered = filter_pd_effects_to_evidence_backed(
        "clarithromycin",
        effects,
    )

    assert filtered == [
        PDEffect(
            effect_id="nausea",
            direction="increase",
            magnitude="medium",
        )
    ]


def test_filter_facts_to_evidence_backed_pd_effects_filters_only_pd_effects():
    facts = Facts(
        drugs={
            "clarithromycin": Drug(
                id="clarithromycin",
                generic_name="clarithromycin",
                drug_class="macrolide antibiotic",
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
            "clarithromycin": [
                EnzymeRole(
                    enzyme_id="CYP3A4",
                    role="inhibitor",
                    strength="strong",
                )
            ],
        },
        transporter_roles={
            "fluconazole": [
                TransporterRole(
                    transporter_id="P-gp",
                    role="inhibitor",
                    strength="moderate",
                )
            ],
        },
        pd_effects={
            "clarithromycin": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                ),
                PDEffect(
                    effect_id="not_real_effect",
                    direction="increase",
                    magnitude="medium",
                ),
            ],
            "fluconazole": [
                PDEffect(
                    effect_id="nausea",
                    direction="increase",
                    magnitude="medium",
                ),
            ],
        },
    )

    filtered = filter_facts_to_evidence_backed_pd_effects(facts)

    assert filtered.drugs == facts.drugs
    assert filtered.enzyme_roles == facts.enzyme_roles
    assert filtered.transporter_roles == facts.transporter_roles
    assert filtered.pd_effects == {
        "clarithromycin": [
            PDEffect(
                effect_id="nausea",
                direction="increase",
                magnitude="medium",
            )
        ],
        "fluconazole": [
            PDEffect(
                effect_id="nausea",
                direction="increase",
                magnitude="medium",
            )
        ],
    }


def test_filter_facts_to_evidence_backed_pd_effects_does_not_mutate_input():
    facts = Facts(
        drugs={
            "clarithromycin": Drug(
                id="clarithromycin",
                generic_name="clarithromycin",
                drug_class="macrolide antibiotic",
                therapeutic_index="moderate",
            ),
        },
        enzyme_roles={},
        transporter_roles={},
        pd_effects={
            "clarithromycin": [
                PDEffect(
                    effect_id="not_real_effect",
                    direction="increase",
                    magnitude="medium",
                ),
            ],
        },
    )

    filtered = filter_facts_to_evidence_backed_pd_effects(facts)

    assert facts.pd_effects == {
        "clarithromycin": [
            PDEffect(
                effect_id="not_real_effect",
                direction="increase",
                magnitude="medium",
            ),
        ],
    }
    assert filtered.pd_effects == {}