from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

EXPORT_DIR = Path("exports/medications")


def split_csv(value: str) -> list[str]:
    """Split comma-separated input into clean non-empty values."""
    return [item.strip() for item in value.split(",") if item.strip()]


def split_lines(value: str) -> list[str]:
    """Split textarea input into clean non-empty lines."""
    return [line.strip() for line in value.splitlines() if line.strip()]


def build_medication_payload(
    generic_name: str,
    brand_names: str,
    aliases: str,
    drug_class: str,
    categories: str,
    pd_effects: str,
    targets: str,
    enzymes: str,
    external_identifiers: str,
    atc_codes: str,
    pathways: str,
    notes: str,
) -> dict:
    """Build a contributor medication payload from form fields."""
    return {
        "generic_name": generic_name.strip(),
        "brand_names": split_csv(brand_names),
        "aliases": split_csv(aliases),
        "drug_class": drug_class.strip() or None,
        "categories": split_csv(categories),
        "pd_effects": split_lines(pd_effects),
        "targets": split_lines(targets),
        "enzymes": split_lines(enzymes),
        "external_identifiers": split_lines(external_identifiers),
        "atc_codes": split_csv(atc_codes),
        "pathways": split_lines(pathways),
        "notes": notes.strip() or None,
    }


def validate_payload(payload: dict) -> list[str]:
    """Return validation errors for contributor medication payload."""
    errors = []

    if not payload["generic_name"]:
        errors.append("Generic name is required.")

    if not payload["pd_effects"]:
        errors.append("At least one PD effect is recommended.")

    return errors


def export_payload(payload: dict) -> Path:
    """Export medication payload to a local JSON file."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = payload["generic_name"].lower().replace(" ", "_")
    output_path = EXPORT_DIR / f"{safe_name}.json"

    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    st.set_page_config(
        page_title="Medication Contributor Form",
        page_icon="💊",
        layout="wide",
    )

    st.title("Medication Contributor Form")
    st.caption(
        "Generate reviewed medication JSON. This does not write directly "
        "to the database."
    )

    with st.form("medication_form"):
        generic_name = st.text_input("Generic name *")

        brand_names = st.text_input(
            "Brand names",
            help="Comma-separated. Example: Wellbutrin, Zyban",
        )

        aliases = st.text_input(
            "Aliases",
            help="Comma-separated search aliases.",
        )

        drug_class = st.text_input(
            "Drug class",
            help="Example: NDRI, SSRI, benzodiazepine",
        )

        categories = st.text_input(
            "Categories",
            help="Comma-separated. Example: antidepressant, smoking cessation",
        )

        pd_effects = st.text_area(
            "PD effects",
            help="One per line. Example: insomnia, nausea, CNS_depression",
        )

        targets = st.text_area(
            "Targets",
            help="One per line. Example: NET, DAT, SERT",
        )

        enzymes = st.text_area(
            "Enzymes",
            help="One per line. Example: CYP2D6 inhibitor",
        )

        external_identifiers = st.text_area(
            "External identifiers",
            help="One per line. Example: DrugBank: DB01156",
        )

        atc_codes = st.text_input(
            "ATC codes",
            help="Comma-separated. Example: N06AX12",
        )

        pathways = st.text_area(
            "Pathways",
            help="One per line.",
        )

        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Preview JSON")

    if not submitted:
        return

    payload = build_medication_payload(
        generic_name=generic_name,
        brand_names=brand_names,
        aliases=aliases,
        drug_class=drug_class,
        categories=categories,
        pd_effects=pd_effects,
        targets=targets,
        enzymes=enzymes,
        external_identifiers=external_identifiers,
        atc_codes=atc_codes,
        pathways=pathways,
        notes=notes,
    )

    errors = validate_payload(payload)

    if errors:
        st.error("Please fix the following issues:")
        for error in errors:
            st.write(f"- {error}")
        return

    payload_json = json.dumps(payload, indent=2, sort_keys=True)

    st.subheader("Medication JSON Preview")
    st.code(payload_json, language="json")

    st.download_button(
        label="Download JSON",
        data=payload_json + "\n",
        file_name=f"{payload['generic_name'].lower().replace(' ', '_')}.json",
        mime="application/json",
    )

    if st.button("Export JSON to local project folder"):
        output_path = export_payload(payload)
        st.success(f"Exported to {output_path}")


if __name__ == "__main__":
    main()