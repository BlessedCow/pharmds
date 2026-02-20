from __future__ import annotations

from collections import defaultdict

from core.constants import PD_EFFECT_CNS_DEP, TRANSPORTER_PGP
from core.enums import Domain, RuleClass, Severity
from core.models import Facts, RuleHit

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


def _pair_key(h: RuleHit) -> tuple[str, str] | None:
    inputs = h.inputs or {}
    a = inputs.get("A")
    b = inputs.get("B")
    if not a or not b:
        return None
    return (a, b)


def _escalate_severity_for_multi_mech(
    base: Severity,
    *,
    mech_count: int,
    enabled: bool,
) -> Severity:
    """
    Conservative escalation policy:
    - Only applies when enabled and mech_count >= 2
    - Bump caution -> major
    - Leave major/contraindicated unchanged
    """
    if not enabled:
        return base
    if mech_count < 2:
        return base
    if base == Severity.caution:
        return Severity.major
    return base


def _pk_mechanisms_for_hit(h: RuleHit) -> set[str]:
    """
    Extract mechanism labels from a PK RuleHit.
    Conservative: only uses existing fields (inputs enzyme_id/transporter_id).
    """
    if h.domain != Domain.PK:
        return set()

    inputs = h.inputs or {}
    out: set[str] = set()

    enzyme_id = inputs.get("enzyme_id")
    if isinstance(enzyme_id, str):
        eid = enzyme_id.upper()
        if eid.startswith("CYP"):
            out.add("cyp")
        elif eid.startswith("UGT"):
            out.add("ugt")

    transporter_id = inputs.get("transporter_id")
    if transporter_id == TRANSPORTER_PGP:
        out.add("pgp")
    elif isinstance(transporter_id, str) and transporter_id:
        out.add(transporter_id.lower())

    return out


def _rule_id_for_mechs(mechs: set[str]) -> str:
    """
    Preserve existing IDs for common dual-mechanism cases.
    """
    if mechs == {"cyp", "pgp"}:
        return "PK_DUAL_MECH_INCREASE"
    if mechs == {"cyp", "ugt"}:
        return "PK_DUAL_MECH_INCREASE_CYP_UGT"
    if mechs == {"ugt", "pgp"}:
        return "PK_DUAL_MECH_INCREASE_UGT_PGP"
    return "PK_MULTI_MECH_INCREASE"


def _label_for_mechs(mechs: set[str]) -> str:
    order = ["cyp", "ugt", "pgp"]
    pretty = {"cyp": "CYP", "ugt": "UGT", "pgp": "P-gp"}

    parts: list[str] = [pretty[k] for k in order if k in mechs]

    extras = sorted(m for m in mechs if m not in set(order))
    parts.extend(extras)

    return " + ".join(parts) if parts else "multiple PK"


def apply_pk_multi_mechanism_exposure_increase(
    facts: Facts,
    hits: list[RuleHit],
    *,
    min_mechanisms: int = 2,
    escalate_severity: bool = False,
) -> list[RuleHit]:
    """
    General composite: if >= min_mechanisms distinct PK exposure-increase mechanisms
    are present for the same (A,B), emit a composite hit.

    Severity escalation is optional and conservative (off by default).
    """
    by_pair: dict[tuple[str, str], list[RuleHit]] = defaultdict(list)
    for h in hits:
        if h.domain != Domain.PK:
            continue
        if "exposure_increase" not in (h.tags or []):
            continue
        key = _pair_key(h)
        if key:
            by_pair[key].append(h)

    out = hits[:]

    for (a, b), pair_hits in by_pair.items():
        mechs: set[str] = set()
        for h in pair_hits:
            mechs.update(_pk_mechanisms_for_hit(h))

        if len(mechs) < min_mechanisms:
            continue

        rid = _rule_id_for_mechs(mechs)
        label = _label_for_mechs(mechs)

        already = any(
            h.domain == Domain.PK
            and h.rule_id == rid
            and (h.inputs or {}).get("A") == a
            and (h.inputs or {}).get("B") == b
            for h in out
        )
        if already:
            continue

        base_sev = _max_sev(pair_hits)
        sev = _escalate_severity_for_multi_mech(
            base_sev,
            mech_count=len(mechs),
            enabled=escalate_severity,
        )
        cls = _max_class(pair_hits)

        rationale: list[str] = [
            f"More than one exposure-increasing PK mechanism is present ({label}).",
            "Multiple exposure-increasing mechanisms may increase risk more than either mechanism alone in some contexts.",
        ]
        if sev != base_sev:
            rationale.append(
                f"Composite severity escalated from {base_sev.value} to {sev.value} due to multiple mechanisms."
            )

        is_dual = len(mechs) == 2
        tags = ["exposure_increase", "multi_mechanism"]
        if is_dual:
            tags.append("dual_mechanism")

        out.append(
            RuleHit(
                rule_id=rid,
                name=f"Multiple PK mechanisms may increase exposure ({label})",
                domain=Domain.PK,
                severity=sev,
                rule_class=cls,
                inputs={"A": a, "B": b},
                tags=tags,
                rationale=rationale,
                actions=[
                    "Use extra caution when multiple exposure-increasing mechanisms apply.",
                    "Consider alternatives, dose adjustment, and closer monitoring when clinically appropriate.",
                ],
                references=[
                    {
                        "source": "Educational note",
                        "citation": "Multiple PK mechanisms can be additive or synergistic.",
                    }
                ],
            )
        )

    return out


# Compatibility wrappers for existing tests / older call sites.
# These are now aliases to the generalized engine.
def apply_pk_dual_mechanism(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    return apply_pk_multi_mechanism_exposure_increase(
        facts,
        hits,
        min_mechanisms=2,
        escalate_severity=False,
    )


def apply_pk_cyp_ugt(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    return apply_pk_multi_mechanism_exposure_increase(
        facts,
        hits,
        min_mechanisms=2,
        escalate_severity=False,
    )


def apply_pk_ugt_pgp(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    return apply_pk_multi_mechanism_exposure_increase(
        facts,
        hits,
        min_mechanisms=2,
        escalate_severity=False,
    )


def apply_composites(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    out = hits[:]

    # PK -> PD composite (CNS depression amplification)
    pk_up_pairs: list[tuple[str, str]] = []
    for h in out:
        if h.domain != Domain.PK:
            continue
        if "exposure_increase" not in (h.tags or []):
            continue
        key = _pair_key(h)
        if key:
            pk_up_pairs.append(key)

    seen: set[tuple[str, str]] = set()
    for affected_a, interacting_b in pk_up_pairs:
        key = (affected_a, interacting_b)
        if key in seen:
            continue
        seen.add(key)

        has_cns = any(
            e.effect_id == PD_EFFECT_CNS_DEP and e.magnitude in ("medium", "high")
            for e in facts.pd_effects.get(affected_a, [])
        )
        if not has_cns:
            continue

        out.append(
            RuleHit(
                rule_id="COMP_PK_UP_CNS_DEP",
                name="Increased exposure may amplify CNS depression effects",
                domain=Domain.PD,
                severity=Severity.major,
                rule_class=RuleClass.adjust_monitor,
                actions=[
                    "Use caution with sedation and impairment risk.",
                    "Consider reducing overlapping sedatives and monitoring for oversedation (educational).",
                ],
                inputs={"A": affected_a, "B": interacting_b},
                rationale=[
                    "{A_name} has CNS-depressant effects.",
                    "Rules indicate increased exposure of {A_name}, which may amplify sedation-related adverse effects.",
                ],
                references=[
                    {
                        "source": "Educational note",
                        "citation": "Composite: PK exposure increase can amplify PD effects.",
                    }
                ],
                tags=["composite", "cns_depression_amplified"],
            )
        )

    # Escalation OFF by default for stable output.
    out = apply_pk_multi_mechanism_exposure_increase(
        facts,
        out,
        min_mechanisms=2,
        escalate_severity=False,
    )

    return out
