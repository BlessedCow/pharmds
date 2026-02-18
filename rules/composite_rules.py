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


def _mech_label(requires: set[str]) -> str:
    parts: list[str] = []
    if "has_cyp" in requires:
        parts.append("CYP")
    if "has_ugt" in requires:
        parts.append("UGT")
    if "has_pgp" in requires:
        parts.append("P-gp")
    return " + ".join(parts) if parts else "multiple PK"


def _mech_rule_id(requires: set[str]) -> str:
    # Keep the existing rule_id for backwards compatibility
    if requires == {"has_cyp", "has_pgp"}:
        return "PK_DUAL_MECH_INCREASE"
    if requires == {"has_cyp", "has_ugt"}:
        return "PK_DUAL_MECH_INCREASE_CYP_UGT"
    if requires == {"has_ugt", "has_pgp"}:
        return "PK_DUAL_MECH_INCREASE_UGT_PGP"
    return "PK_MULTI_MECH_INCREASE"


def apply_pk_composites(
    facts: Facts,
    hits: list[RuleHit],
    *,
    required_tags: set[str],
    requires: set[str],
) -> list[RuleHit]:
    """
    Generalized PK composite framework that matches your current RuleHit structure.

    - Groups candidate hits by (A, B) from hit.inputs
    - Filters to Domain.PK + required tags (exposure_increase)
    - Checks for presence of mechanisms listed in `requires`
      (ex: {"has_cyp", "has_pgp"})
    - Emits one composite hit per (A, B)
    """
    by_pair: dict[tuple[str, str], list[RuleHit]] = defaultdict(list)
    for h in hits:
        if h.domain != Domain.PK:
            continue
        tags = set(h.tags or [])
        if not required_tags.issubset(tags):
            continue
        key = _pair_key(h)
        if key:
            by_pair[key].append(h)

    out = hits[:]

    rid = _mech_rule_id(requires)
    label = _mech_label(requires)

    for (a, b), pair_hits in by_pair.items():
        sev = _max_sev(pair_hits)
        cls = _max_class(pair_hits)

        has_cyp = any(
            isinstance((h.inputs or {}).get("enzyme_id"), str)
            and ((h.inputs or {}).get("enzyme_id") or "").startswith("CYP")
            for h in pair_hits
        )
        has_ugt = any(
            isinstance((h.inputs or {}).get("enzyme_id"), str)
            and ((h.inputs or {}).get("enzyme_id") or "").startswith("UGT")
            for h in pair_hits
        )
        has_pgp = any(
            (h.inputs or {}).get("transporter_id") == TRANSPORTER_PGP
            for h in pair_hits
        )

        pred_map = {
            "has_cyp": has_cyp,
            "has_ugt": has_ugt,
            "has_pgp": has_pgp,
        }
        if not all(pred_map.get(req, False) for req in requires):
            continue

        # Avoid duplicates if apply_composites is called multiple times
        already = any(
            h.domain == Domain.PK
            and h.rule_id == rid
            and (h.inputs or {}).get("A") == a
            and (h.inputs or {}).get("B") == b
            for h in out
        )
        if already:
            continue

        out.append(
            RuleHit(
                rule_id=rid,
                name=f"Dual-mechanism exposure increase ({label})",
                domain=Domain.PK,
                severity=sev,
                rule_class=cls,
                inputs={"A": a, "B": b},
                tags=["exposure_increase", "dual_mechanism"],
                rationale=[
                    f"More than one exposure-increasing mechanism is present ({label}).",
                    "Multiple exposure-increasing mechanisms may increase risk more than either mechanism alone in some contexts.",
                ],
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


def apply_pk_dual_mechanism(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    """
    Backwards compatible wrapper that preserves existing behavior:
    CYP + P-gp dual mechanism composite, based on exposure_increase hits.
    """
    return apply_pk_composites(
        facts,
        hits,
        required_tags={"exposure_increase"},
        requires={"has_cyp", "has_pgp"},
    )

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
    # Pretty label for name/rationale
    order = ["cyp", "ugt", "pgp"]
    pretty = {
        "cyp": "CYP",
        "ugt": "UGT",
        "pgp": "P-gp",
    }
    parts: list[str] = []
    for k in order:
        if k in mechs:
            parts.append(pretty[k])

    # include any other transporters we might add later
    extras = sorted(m for m in mechs if m not in set(order))
    parts.extend(extras)

    return " + ".join(parts) if parts else "multiple PK"


def apply_pk_multi_mechanism_exposure_increase(
    facts: Facts,
    hits: list[RuleHit],
    *,
    min_mechanisms: int = 2,
) -> list[RuleHit]:
    """
    General composite: if >= min_mechanisms distinct PK exposure-increase mechanisms
    are present for the same (A,B), emit a composite hit.

    - Groups by (A,B)
    - Considers only Domain.PK hits with tag "exposure_increase"
    - Mechanisms derived from enzyme_id/transporter_id
    - Emits at most one composite per (A,B)
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
        # build distinct mechanism set across all contributing hits
        mechs: set[str] = set()
        for h in pair_hits:
            mechs.update(_pk_mechanisms_for_hit(h))

        if len(mechs) < min_mechanisms:
            continue

        rid = _rule_id_for_mechs(mechs)
        label = _label_for_mechs(mechs)

        # De-dupe: any existing composite with same (A,B) and rule_id
        already = any(
            h.domain == Domain.PK
            and h.rule_id == rid
            and (h.inputs or {}).get("A") == a
            and (h.inputs or {}).get("B") == b
            for h in out
        )
        if already:
            continue

        sev = _max_sev(pair_hits)
        cls = _max_class(pair_hits)

        out.append(
            RuleHit(
                rule_id=rid,
                name=f"Multiple PK mechanisms may increase exposure ({label})",
                domain=Domain.PK,
                severity=sev,
                rule_class=cls,
                inputs={"A": a, "B": b},
                tags=["exposure_increase", "multi_mechanism"],
                rationale=[
                    f"More than one exposure-increasing PK mechanism is present ({label}).",
                    "Multiple exposure-increasing mechanisms may increase risk more than either mechanism alone in some contexts.",
                ],
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

# Ready-to-enable wrappers (do not call them yet)
def apply_pk_cyp_ugt(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    return apply_pk_composites(
        facts,
        hits,
        required_tags={"exposure_increase"},
        requires={"has_cyp", "has_ugt"},
    )


def apply_pk_ugt_pgp(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    return apply_pk_composites(
        facts,
        hits,
        required_tags={"exposure_increase"},
        requires={"has_ugt", "has_pgp"},
    )


def apply_composites(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    out = hits[:]

    # Collect causal PK exposure increases as (affected_A, interacting_B)
    pk_up_pairs: list[tuple[str, str]] = []
    for h in out:
        if h.domain != Domain.PK:
            continue
        if "exposure_increase" not in (h.tags or []):
            continue
        key = _pair_key(h)
        if key:
            pk_up_pairs.append(key)

    # Emit at most one composite per causal pair
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

    out = apply_pk_multi_mechanism_exposure_increase(facts, out, min_mechanisms=2)
    return out
