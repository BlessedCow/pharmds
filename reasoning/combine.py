from __future__ import annotations

from collections import defaultdict

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
) -> list[PairReport]:
    """
    Group by unordered pair (stable by drug_id ordering), then split into PK/PD sections.
    PK hits remain directional (A affected, B interacting) and should be displayed as such.
    """
    grouped: dict[tuple[str, str], list[RuleHit]] = defaultdict(list)

    for h in hits:
        a = h.inputs["A"]
        b = h.inputs["B"]
        d1, d2 = (a, b) if a < b else (b, a)
        grouped[(d1, d2)].append(h)

    reports: list[PairReport] = []
    for (d1, d2), pair_hits in grouped.items():
        pk_hits = [h for h in pair_hits if h.domain == Domain.PK]
        pd_hits = [h for h in pair_hits if h.domain == Domain.PD]

        pk_out = _dedupe_hits(pk_hits, facts, rule_templates)
        pd_out = _dedupe_hits(pd_hits, facts, rule_templates)

        overall = pair_hits[:]  # all hits drive overall labels
        rep = PairReport(
            drug_1=d1,
            drug_2=d2,
            overall_severity=_max_sev(overall),
            overall_rule_class=_max_class(overall),
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
