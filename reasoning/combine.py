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

def build_regimen_summary(facts: Facts, pair_reports: list[PairReport]) -> dict:
    drug_ids = list(facts.drugs.keys())
    """
    Build a regimen-level summary across all drugs in the input, beyond pairwise.

    Returns a dict so we don't have to change models yet.
    """
    # Aggregate all hits across all pairs
    all_hits: list[RuleHit] = []
    for rep in pair_reports:
        all_hits.extend(rep.pk_hits)
        all_hits.extend(rep.pd_hits)

    # Base severity/class from pairwise (if any)
    if all_hits:
        overall_sev = max((h.severity for h in all_hits), key=lambda s: _SEV_RANK[s])
        overall_cls = _effective_overall_class(all_hits, overall_sev)
    else:
        overall_sev = Severity.info
        overall_cls = RuleClass.info

    # --- Regimen-level PD stacking: 3+ drugs with same PD effect >= medium ---
    # This uses Drug.pd_effects from Facts (same objects used for pd_overlap).
    effect_counts: Counter[str] = Counter()
    for did in drug_ids:
        for e in (facts.pd_effects.get(did, []) or []):
            # Expect e.effect_id and e.magnitude based on rule logic
            if getattr(e, "effect_id", None) == "CNS_depression" and getattr(e, "magnitude", None) in {"medium", "high"}:
                effect_counts["CNS_depression"] += 1
            if getattr(e, "effect_id", None) == "QT_prolongation" and getattr(e, "magnitude", None) in {"medium", "high"}:
                effect_counts["QT_prolongation"] += 1

    regimen_flags: list[dict] = []

    # CNS triple stack escalation
    if effect_counts["CNS_depression"] >= 3:
        regimen_flags.append(
            {
                "type": "PD_STACK",
                "effect_id": "CNS_depression",
                "count": effect_counts["CNS_depression"],
                "message": "3+ drugs in the regimen contribute to CNS depression (medium+). Consider avoiding the combination or using intensive monitoring.",
                "suggested_class": "avoid",
                "suggested_severity": "contraindicated",
            }
        )
        overall_cls = RuleClass.avoid
        overall_sev = Severity.contraindicated

    # QT triple stack escalation
    if effect_counts["QT_prolongation"] >= 3:
        regimen_flags.append(
            {
                "type": "PD_STACK",
                "effect_id": "QT_prolongation",
                "count": effect_counts["QT_prolongation"],
                "message": "3+ drugs in the regimen contribute to QT prolongation risk (medium+). Consider avoiding or use ECG monitoring and risk mitigation.",
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
        "pairwise_hit_count": len(all_hits),
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
