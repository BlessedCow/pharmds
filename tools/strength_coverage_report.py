"""Print coverage of source-linked product strength options by substance."""

from __future__ import annotations

from data.loaders import load_drugs_curation


def main() -> None:
    drugs = load_drugs_curation()["drugs"]
    covered = sum(bool(drug.get("dosage_options")) for drug in drugs)
    count = sum(len(drug.get("dosage_options") or []) for drug in drugs)
    print("# Sourced product strength coverage")
    print()
    print(f"{count} reference options across {covered} of {len(drugs)} substances.")
    print()
    print(
        "A blank row is a curation gap. Options describe the named product or study "
        "formulation and are not recommended doses or an exhaustive market inventory."
    )
    print()
    print("| Substance | Strength options | Route and release covered |")
    print("| --- | ---: | --- |")
    for drug in drugs:
        options = drug.get("dosage_options") or []
        forms = sorted({f"{o['route']} {o['release_type']}" for o in options})
        print(f"| `{drug['id']}` | {len(options)} | {', '.join(forms) or 'Pending'} |")


if __name__ == "__main__":
    main()
