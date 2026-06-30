from __future__ import annotations

from rules.engine import rule_mechanisms


def _parse_domain_selection(domain_arg: str) -> list[str]:
    raw = (domain_arg or "all").strip().lower()
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    selected: list[str] = []

    def add(value: str) -> None:
        if value not in selected:
            selected.append(value)

    for part in parts:
        if part == "all":
            add("cyp")
            add("ugt")
            add("pgp")
            add("bcrp")
            add("oatp")
            add("named_pair")
            add("pd")
        elif part == "pk":
            add("cyp")
            add("ugt")
            add("pgp")
            add("bcrp")
            add("oatp")
            add("named_pair")
        elif part == "pd":
            add("pd")
        elif part == "cyp":
            add("cyp")
        elif part == "pgp":
            add("pgp")
        elif part == "bcrp":
            add("bcrp")
        elif part == "oatp":
            add("oatp")
        elif part == "ugt":
            add("ugt")
        elif part == "sert":
            add("SERT")
        elif part == "net":
            add("NET")
        else:
            raise SystemExit(
                "Unknown --domain option. Use: all, pk, pd, cyp, ugt, "
                "pgp, bcrp, oatp"
            )

    if not selected:
        selected = ["cyp", "ugt", "pgp", "bcrp", "oatp", "named_pair", "pd"]

    return selected


def filter_rules_for_selected_domains(rules_all, selected: list[str]):
    """
    Filter rules for the CLI-selected domains.

    Here, domains are user-facing slices based on rule mechanism tags:
      - cyp: CYP-mediated PK rules
      - pgp: P-gp transporter PK rules
      - pd: PD effect stacking rules
    """
    selected_set = set(selected)
    out = []

    for rule in rules_all:
        mechanisms = set(rule_mechanisms(rule))
        if mechanisms & selected_set:
            out.append(rule)

    return out