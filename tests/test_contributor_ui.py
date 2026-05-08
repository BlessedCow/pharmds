from app.contributor_ui import (
    build_medication_payload,
    split_csv,
    split_lines,
    validate_payload,
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