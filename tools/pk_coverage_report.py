"""Print current drug and formulation coverage of sourced PK observations."""

from __future__ import annotations

from collections import Counter

from data.curation.pk_observations import load_pk_curation
from data.loaders import load_drugs_curation


def coverage_rows() -> tuple[tuple[str, int, int, int], ...]:
    """Return drug ID, covered formulation count, total formulations, observations."""
    catalog = load_drugs_curation()["drugs"]
    _, observations = load_pk_curation()
    measured = {(o.drug_id, o.route, o.release_type) for o in observations}
    counts = Counter(o.drug_id for o in observations)
    rows = []
    for drug in catalog:
        forms = {
            (drug["id"], form["route"], release)
            for form in drug.get("formulations", [])
            for release in form.get("release_types", [])
        }
        rows.append(
            (
                drug["id"],
                len(forms & measured),
                len(forms),
                counts[drug["id"]],
            )
        )
    return tuple(rows)


def main() -> None:
    rows = coverage_rows()
    measured_drugs = sum(count > 0 for _, _, _, count in rows)
    measured_forms = sum(covered for _, covered, _, _ in rows)
    total_forms = sum(total for _, _, total, _ in rows)
    print("# Sourced PK coverage")
    print()
    print(
        f"{measured_drugs} of {len(rows)} substances have at least one "
        f"source-linked observation. {measured_forms} of {total_forms} "
        "route and release combinations have an observation."
    )
    print()
    print("A pending row is a curation gap, not evidence that PK data does not exist.")
    print()
    print("| Substance | Formulations covered | Observations |")
    print("| --- | ---: | ---: |")
    for drug_id, covered, total, count in rows:
        print(f"| `{drug_id}` | {covered}/{total} | {count} |")


if __name__ == "__main__":
    main()
