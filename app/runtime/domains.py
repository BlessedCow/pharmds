from __future__ import annotations

from core.models import Facts
from core.pd_effect_families import pd_effects_share_family
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


def filter_rules_for_selected_pd_effects(
    rules,
    selected_pd_effects: list[str] | None,
):
    if not selected_pd_effects:
        return list(rules)

    filtered = []

    for rule in rules:
        logic = rule.logic or {}
        pd_overlap = logic.get("pd_overlap")

        if pd_overlap is not None:
            effect_id = pd_overlap.get("effect_id")
        elif getattr(rule.domain, "value", rule.domain) == "PD":
            effect_id = logic.get("effect_id")
        else:
            filtered.append(rule)
            continue

        if effect_id and any(
            pd_effects_share_family(effect_id, selected_effect)
            for selected_effect in selected_pd_effects
        ):
            filtered.append(rule)

    return filtered

def filter_facts_for_selected_pd_effects(
    facts: Facts,
    selected_pd_effects: list[str] | None,
) -> Facts:
    if not selected_pd_effects:
        return facts

    filtered_pd_effects = {
        drug_id: [
            effect
            for effect in effects
            if any(
                pd_effects_share_family(effect.effect_id, selected_effect)
                for selected_effect in selected_pd_effects
            )
        ]
        for drug_id, effects in facts.pd_effects.items()
    }

    filtered_pd_effects = {
        drug_id: effects
        for drug_id, effects in filtered_pd_effects.items()
        if effects
    }

    return Facts(
        drugs=facts.drugs,
        enzyme_roles=facts.enzyme_roles,
        transporter_roles=facts.transporter_roles,
        pd_effects=filtered_pd_effects,
        patient_flags=facts.patient_flags,
    )
