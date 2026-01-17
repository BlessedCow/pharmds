from __future__ import annotations

from typing import List, Tuple, Set

from core.enums import Domain, Severity, RuleClass
from core.models import Facts, RuleHit


def apply_composites(facts: Facts, hits: List[RuleHit]) -> List[RuleHit]:
    out = hits[:]

    # Collect causal PK exposure increases as (affected_A, interacting_B)
    pk_up_pairs: List[Tuple[str, str]] = []
    for h in hits:
        if h.domain != Domain.PK:
            continue
        if "exposure_increase" in h.tags:
            pk_up_pairs.append((h.inputs["A"], h.inputs["B"]))

    # Emit at most one composite per causal pair
    seen: Set[Tuple[str, str]] = set()

    for affected_a, interacting_b in pk_up_pairs:
        key = (affected_a, interacting_b)
        if key in seen:
            continue
        seen.add(key)

        has_cns = any(
            e.effect_id == "CNS_depression" and e.magnitude in ("medium", "high")
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

    return out
