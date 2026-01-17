 # explanation templating, trace -> prose
 
from __future__ import annotations
from typing import Dict
from core.models import Facts, RuleHit


def _drug_name(facts: Facts, drug_id: str) -> str:
    d = facts.drugs.get(drug_id)
    return d.generic_name if d else drug_id


def render_explanation(template: str, facts: Facts, hit: RuleHit) -> str:
    mapping: Dict[str, str] = {
        "A_name": _drug_name(facts, hit.inputs["A"]),
        "B_name": _drug_name(facts, hit.inputs["B"]),
    }
    # Extra fields (enzyme_id, transporter_id, effect_id)
    for k, v in hit.inputs.items():
        if k in ("A", "B"):
            continue
        mapping[k] = str(v)

    text = template
    for key, val in mapping.items():
        text = text.replace("{" + key + "}", val)
    return text


def render_rationale(facts: Facts, hit: RuleHit) -> str:
    if not hit.rationale:
        return ""
    A = _drug_name(facts, hit.inputs["A"])
    B = _drug_name(facts, hit.inputs["B"])

    bullets = []
    for line in hit.rationale:
        bullets.append(f"- {line.replace('A', A).replace('B', B)}")
    return "\n".join(bullets)