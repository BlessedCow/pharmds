from app.contributor_ui import (
    build_medication_payload,
    canonicalize_pd_effect,
    canonicalize_pd_effects,
    split_csv,
    split_lines,
    validate_payload,
    validate_pd_effects,
)


def test_split_csv_cleans_values():
    assert split_csv("Wellbutrin, Zyban, ") == ["Wellbutrin", "Zyban"]


def test_split_lines_cleans_values():
    assert split_lines("insomnia\n\nnausea\n ") == ["insomnia", "nausea"]


def test_build_medication_payload_from_fields():
    payload = build_medication_payload(
        generic_name="bupropion",
        brand_names="Wellbutrin, Zyban",
        aliases="wellbutrin sr, wellbutrin xl",
        drug_class="NDRI",
        categories="antidepressant, smoking cessation",
        pd_effects="insomnia\nnausea",
        targets="NET\nDAT",
        enzymes="CYP2D6 inhibitor",
        external_identifiers="DrugBank: DB01156",
        atc_codes="N06AX12",
        pathways="dopamine reuptake inhibition",
        notes="Test note",
    )

    assert payload["generic_name"] == "bupropion"
    assert payload["brand_names"] == ["Wellbutrin", "Zyban"]
    assert payload["aliases"] == ["wellbutrin sr", "wellbutrin xl"]
    assert payload["drug_class"] == "NDRI"
    assert payload["categories"] == ["antidepressant", "smoking cessation"]
    assert payload["pd_effects"] == ["insomnia", "nausea"]
    assert payload["targets"] == ["NET", "DAT"]
    assert payload["enzymes"] == ["CYP2D6 inhibitor"]
    assert payload["external_identifiers"] == ["DrugBank: DB01156"]
    assert payload["atc_codes"] == ["N06AX12"]
    assert payload["pathways"] == ["dopamine reuptake inhibition"]
    assert payload["notes"] == "Test note"


def test_validate_payload_requires_generic_name():
    payload = {
        "generic_name": "",
        "pd_effects": ["insomnia"],
    }

    assert "Generic name is required." in validate_payload(payload)


def test_validate_payload_recommends_pd_effects():
    payload = {
        "generic_name": "bupropion",
        "pd_effects": [],
    }

    assert "At least one PD effect is recommended." in validate_payload(payload)
    
def test_canonicalize_pd_effect_accepts_canonical_value():
    assert canonicalize_pd_effect("CNS_depression") == "CNS_depression"


def test_canonicalize_pd_effect_maps_alias():
    assert canonicalize_pd_effect("cns depression") == "CNS_depression"


def test_validate_pd_effects_accepts_known_effects():
    assert validate_pd_effects(["CNS_depression", "sedation"]) == []


def test_validate_pd_effects_warns_with_suggestion():
    errors = validate_pd_effects(["respiratory depression"])

    assert errors == [
        "Unknown PD effect 'respiratory depression'. "
        "Did you mean 'respiratory_depression'?"
    ]


def test_validate_pd_effects_warns_without_suggestion():
    errors = validate_pd_effects(["made_up_effect"])

    assert errors == ["Unknown PD effect 'made_up_effect'."]
    
def test_canonicalize_pd_effects_maps_aliases_and_preserves_unknowns():
    assert canonicalize_pd_effects(
        ["respiratory depression", "sedating", "made_up_effect"]
    ) == ["respiratory_depression", "sedation", "made_up_effect"]


def test_canonicalize_pd_effects_preserves_canonical_values():
    assert canonicalize_pd_effects(
        ["respiratory_depression", "sedation"]
    ) == ["respiratory_depression", "sedation"]