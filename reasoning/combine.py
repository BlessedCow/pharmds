from __future__ import annotations

from collections import Counter, defaultdict

from core.enums import Domain, RuleClass, Severity
from core.models import Facts, PairReport, RuleHit
from reasoning.explain import render_explanation

_SEV_RANK = {
    Severity.info: 0,
    Severity.caution: 1,
    Severity.major: 2,
    Severity.contraindicated: 3,
}

_CLASS_RANK = {
    RuleClass.info: 0,
    RuleClass.caution: 1,
    RuleClass.adjust_monitor: 2,
    RuleClass.avoid: 3,
}


def _max_sev(hits: list[RuleHit]) -> Severity:
    return max((h.severity for h in hits), key=lambda s: _SEV_RANK[s])


def _max_class(hits: list[RuleHit]) -> RuleClass:
    return max((h.rule_class for h in hits), key=lambda c: _CLASS_RANK[c])

def _default_class_for_severity(sev: Severity) -> RuleClass:
    """
    Default action bucket for a given severity.
    This is used as a floor (we never downgrade below this).
    """
    return {
        Severity.info: RuleClass.info,
        Severity.caution: RuleClass.caution,
        Severity.major: RuleClass.adjust_monitor,
        Severity.contraindicated: RuleClass.avoid,
    }[sev]


def _bump_class(c: RuleClass) -> RuleClass:
    """Increase class by one step, capped at avoid."""
    order = [
        RuleClass.info,
        RuleClass.caution,
        RuleClass.adjust_monitor,
        RuleClass.avoid,
    ]
    i = order.index(c)
    return order[min(i + 1, len(order) - 1)]


def _effective_overall_class(hits: list[RuleHit], overall_sev: Severity) -> RuleClass:
    """
    Compute a dynamic overall rule class.
    - Start with the max of:
        (a) the strongest class among hits
        (b) the default class implied by overall severity (floor)
    - Then optionally escalate based on context (hit count).
    """
    if not hits:
        return _default_class_for_severity(overall_sev)

    base = _max_class(hits)
    floor = _default_class_for_severity(overall_sev)

    eff = max((base, floor), key=lambda c: _CLASS_RANK[c])

    # Simple dynamic escalation: lots of independent hits -> stronger recommendation
    if len(hits) >= 3:
        eff = _bump_class(eff)

    # Contraindicated always maps to avoid
    if overall_sev == Severity.contraindicated:
        eff = RuleClass.avoid

    return eff

def _value(x: object) -> str:
    """Return enum.value when present, otherwise a string."""
    return str(getattr(x, "value", x))


def _magnitude_rank(magnitude: str | None) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(str(magnitude or ""), -1)


def _medium_or_high(magnitude: str | None) -> bool:
    return _magnitude_rank(magnitude) >= _magnitude_rank("medium")


def _pd_effect_label(effect_id: str) -> str:
    labels = {
        "CNS_depression": "CNS depression",
        "QT_prolongation": "QT prolongation",
        "serotonergic": "serotonergic burden",
        "serotonin_syndrome": "serotonin toxicity risk",
        "bleeding": "bleeding risk",
        "anticholinergic_effects": "anticholinergic burden",
        "orthostatic_hypotension": "orthostatic hypotension",
        "seizure_risk": "seizure risk",
        "sedation": "sedation",
        "nausea": "nausea/GI intolerance",
        "hypertension_risk": "hypertension risk",
        "tachycardia_risk": "tachycardia risk",
        "constipation_risk": "constipation risk",
        "urinary_retention_risk": "urinary retention risk",
    }
    return labels.get(effect_id, effect_id.replace("_", " "))


def _summarize_pd_stacks(facts: Facts) -> list[dict]:
    """
    Summarize repeated medium/high PD effects across the whole regimen.

    Pairwise rules answer "what interacts with what?"
    This answers "what risk domains repeat across the whole list?"
    """
    grouped: dict[str, list[dict]] = defaultdict(list)

    for drug_id in sorted(facts.drugs):
        drug = facts.drugs[drug_id]
        for effect in facts.pd_effects.get(drug_id, []) or []:
            effect_id = getattr(effect, "effect_id", None)
            magnitude = getattr(effect, "magnitude", None)

            if not isinstance(effect_id, str):
                continue

            if not _medium_or_high(magnitude):
                continue

            grouped[effect_id].append(
                {
                    "drug_id": drug_id,
                    "drug_name": drug.generic_name,
                    "magnitude": str(magnitude),
                }
            )

    stacks: list[dict] = []

    for effect_id, contributors in grouped.items():
        if len(contributors) < 2:
            continue

        max_magnitude = max(
            (c["magnitude"] for c in contributors),
            key=_magnitude_rank,
        )

        contributors = sorted(
            contributors,
            key=lambda c: (-_magnitude_rank(c["magnitude"]), c["drug_name"]),
        )

        stacks.append(
            {
                "effect_id": effect_id,
                "label": _pd_effect_label(effect_id),
                "count": len(contributors),
                "max_magnitude": max_magnitude,
                "drugs": contributors,
            }
        )

    stacks.sort(
        key=lambda s: (
            -int(s["count"]),
            -_magnitude_rank(str(s["max_magnitude"])),
            str(s["effect_id"]),
        )
    )

    return stacks


def _summarize_top_pairs(facts: Facts, pair_reports: list[PairReport]) -> list[dict]:
    rows: list[dict] = []

    for rep in pair_reports:
        total_hits = len(rep.pk_hits or []) + len(rep.pd_hits or [])

        rows.append(
            {
                "drug_1": {
                    "id": rep.drug_1,
                    "name": facts.drugs[rep.drug_1].generic_name,
                },
                "drug_2": {
                    "id": rep.drug_2,
                    "name": facts.drugs[rep.drug_2].generic_name,
                },
                "severity": _value(rep.overall_severity),
                "class": _value(rep.overall_rule_class),
                "pk_hits": len(rep.pk_hits or []),
                "pd_hits": len(rep.pd_hits or []),
                "total_hits": total_hits,
            }
        )

    rows.sort(
        key=lambda r: (
            -_SEV_RANK[Severity(r["severity"])],
            -int(r["total_hits"]),
            r["drug_1"]["id"],
            r["drug_2"]["id"],
        )
    )

    return rows[:5]


def build_regimen_summary(facts: Facts, pair_reports: list[PairReport]) -> dict:
    """
    Build a regimen-level summary across all drugs in the input, beyond pairwise.

    Pair reports remain the source of truth for specific interactions. This
    summary gives the UI/CLI a quick regimen-level readout: overall risk,
    repeated PD stacks, pairwise hit counts, and the most important pairs.
    """
    all_hits: list[RuleHit] = []

    for rep in pair_reports:
        all_hits.extend(rep.pk_hits or [])
        all_hits.extend(rep.pd_hits or [])

    if all_hits:
        overall_sev = max((h.severity for h in all_hits), key=lambda s: _SEV_RANK[s])
        overall_cls = _effective_overall_class(all_hits, overall_sev)
    else:
        overall_sev = Severity.info
        overall_cls = RuleClass.info

    hit_counts = {
        "total": len(all_hits),
        "pk": sum(1 for h in all_hits if h.domain == Domain.PK),
        "pd": sum(1 for h in all_hits if h.domain == Domain.PD),
        "by_severity": dict(
            sorted(Counter(_value(h.severity) for h in all_hits).items())
        ),
        "by_class": dict(
            sorted(Counter(_value(h.rule_class) for h in all_hits).items())
        ),
    }

    pd_stacks = _summarize_pd_stacks(facts)
    regimen_flags: list[dict] = []

    high_priority_stack_messages = {
        "CNS_depression": (
            "3+ drugs in the regimen contribute to CNS depression (medium+). "
            "Consider avoiding the combination or using intensive monitoring."
        ),
        "QT_prolongation": (
            "3+ drugs in the regimen contribute to QT prolongation risk (medium+). "
            "Consider avoiding or use ECG monitoring and risk mitigation."
        ),
    }

    for stack in pd_stacks:
        effect_id = stack["effect_id"]
        count = int(stack["count"])

        if effect_id in high_priority_stack_messages and count >= 3:
            regimen_flags.append(
                {
                    "type": "PD_STACK",
                    "effect_id": effect_id,
                    "label": stack["label"],
                    "count": count,
                    "message": high_priority_stack_messages[effect_id],
                    "suggested_class": "avoid",
                    "suggested_severity": "contraindicated",
                }
            )
            overall_cls = RuleClass.avoid
            overall_sev = Severity.contraindicated

    return {
        "n_drugs": len(facts.drugs),
        "overall_severity": overall_sev,
        "overall_rule_class": overall_cls,
        "regimen_flags": regimen_flags,
        "pd_stacks": pd_stacks,
        "pair_count_with_hits": len(pair_reports),
        "pairwise_hit_count": len(all_hits),
        "hit_counts": hit_counts,
        "top_pairs": _summarize_top_pairs(facts, pair_reports),
    }

def _pk_summary(pk_hits: list[RuleHit]) -> str | None:
    inc = any("exposure_increase" in (h.tags or []) for h in pk_hits)
    dec = any("exposure_decrease" in (h.tags or []) for h in pk_hits)

    if inc and dec:
        return "mixed (increase + decrease mechanisms present)"
    if inc:
        return "exposure_increase"
    if dec:
        return "exposure_decrease"
    return None


def build_pair_reports(
    facts: Facts,
    hits: list[RuleHit],
    rule_templates: dict[str, str],
    pairs: list[tuple[str, str]] | None = None,
) -> list[PairReport]:
    """
    Group by unordered pair (stable by drug_id ordering), then split into PK/PD sections.
    PK hits remain directional (A affected, B interacting) and should be displayed as such.
    """
    grouped: dict[tuple[str, str], list[RuleHit]] = defaultdict(list)

    for h in hits:
        a = h.inputs.get("A")
        b = h.inputs.get("B")
        if not a or not b:
            continue
        d1, d2 = (a, b) if a < b else (b, a)
        grouped[(d1, d2)].append(h)

    if pairs is None:
        pair_list = list(grouped.keys())
    else:
        # Normalize requested pairs to the same (min,max) ordering
        pair_list = []
        seen: set[tuple[str, str]] = set()
        for a_id, b_id in pairs:
            d1, d2 = (a_id, b_id) if a_id < b_id else (b_id, a_id)
            if (d1, d2) in seen:
                continue
            seen.add((d1, d2))
            pair_list.append((d1, d2))

    reports: list[PairReport] = []
    for d1, d2 in pair_list:
        pair_hits = grouped.get((d1, d2), [])
        if not pair_hits:
            continue  # keep current semantics: only report pairs with hits

        pk_hits = [h for h in pair_hits if h.domain == Domain.PK]
        pd_hits = [h for h in pair_hits if h.domain == Domain.PD]

        pk_out = _dedupe_hits(pk_hits, facts, rule_templates)
        pd_out = _dedupe_hits(pd_hits, facts, rule_templates)

        overall_sev = _max_sev(pair_hits)
        overall_cls = _effective_overall_class(pair_hits, overall_sev)

        rep = PairReport(
            drug_1=d1,
            drug_2=d2,
            overall_severity=overall_sev,
            overall_rule_class=overall_cls,
            pk_hits=pk_out,
            pd_hits=pd_out,
            pk_summary=_pk_summary(pk_out),
        )
        reports.append(rep)

    reports.sort(key=lambda r: (-_SEV_RANK[r.overall_severity], r.drug_1, r.drug_2))
    return reports


def _dedupe_hits(
    hits: list[RuleHit], facts: Facts, rule_templates: dict[str, str]
) -> list[RuleHit]:
    """
    Optional: dedupe identical hits caused by multiple rules or repeated matches.
    For PK, keep directionality, so dedupe key includes A,B,rule_id.
    For PD, duplicates should already be prevented, but we keep this anyway.
    """
    seen = set()
    out = []
    for h in hits:
        key = (h.rule_id, h.inputs.get("A"), h.inputs.get("B"), h.domain.value)
        if key in seen:
            continue
        seen.add(key)

        # Pre-render explanation for downstream display convenience (optional)
        template = rule_templates.get(h.rule_id, "")
        if template:
            _ = render_explanation(template, facts, h)  # just validates placeholders
        out.append(h)

    out.sort(key=lambda x: (-_SEV_RANK[x.severity], x.rule_id))
    return out

