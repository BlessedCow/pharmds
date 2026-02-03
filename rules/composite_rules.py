from __future__ import annotations

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


def apply_pk_dual_mechanism(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    """
    Add a composite PK hit when both CYP and P-gp exposure-increasing mechanisms
    are present for the same directional pair (A affected, B interacting).

    Option B behavior:
      - severity = max(severity of contributing hits)
      - rule_class = max(rule_class of contributing hits)

    This does NOT remove or replace the original hits.
    """
    pk_hits = [h for h in hits if h.domain == Domain.PK]
    by_pair: dict[tuple[str, str], list[RuleHit]] = {}

    for h in pk_hits:
        a = h.inputs.get("A")
        b = h.inputs.get("B")
        if not a or not b:
            continue
        by_pair.setdefault((a, b), []).append(h)

    out = hits[:]

    for (a, b), pair_hits in by_pair.items():
        inc_hits = [h for h in pair_hits if "exposure_increase" in (h.tags or [])]
        if not inc_hits:
            continue

        has_cyp = any(h.inputs.get("enzyme_id") for h in inc_hits)
        has_pgp = any(
            h.inputs.get("transporter_id") == TRANSPORTER_PGP for h in inc_hits
        )

        if not (has_cyp and has_pgp):
            continue

        sev = _max_sev(inc_hits)
        cls = _max_class(inc_hits)

        out.append(
            RuleHit(
                rule_id="PK_DUAL_MECH_INCREASE",
                name="Dual-mechanism exposure increase (CYP + P-gp)",
                domain=Domain.PK,
                severity=sev,
                rule_class=cls,
                inputs={"A": a, "B": b},
                tags=["exposure_increase", "dual_mechanism"],
                rationale=[
                    "Both metabolic inhibition (CYP) and transporter inhibition (P-gp) mechanisms are present.",
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


def apply_composites(facts: Facts, hits: list[RuleHit]) -> list[RuleHit]:
    out = hits[:]

    # Collect causal PK exposure increases as (affected_A, interacting_B)
    pk_up_pairs: list[tuple[str, str]] = []
    for h in out:
        if h.domain != Domain.PK:
            continue
        if "exposure_increase" in (h.tags or []):
            pk_up_pairs.append((h.inputs["A"], h.inputs["B"]))

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

    out = apply_pk_dual_mechanism(facts, out)
    return out
