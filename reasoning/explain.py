# explanation templating, trace -> prose

from __future__ import annotations

from core.models import Facts, RuleHit


def _drug_name(facts: Facts, drug_id: str) -> str:
    d = facts.drugs.get(drug_id)
    return d.generic_name if d else drug_id


def _format_text(text: str, mapping: dict[str, str]) -> str:
    for k, v in mapping.items():
        text = text.replace("{" + k + "}", v)
    return text


def render_explanation(template: str, facts: Facts, hit: RuleHit) -> str:
    mapping: dict[str, str] = {
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
    mapping = {
        "A_name": _drug_name(facts, hit.inputs["A"]),
        "B_name": _drug_name(facts, hit.inputs["B"]),
        "enzyme_id": str(hit.inputs.get("enzyme_id", "")),
        "transporter_id": str(hit.inputs.get("transporter_id", "")),
        "effect_id": str(hit.inputs.get("effect_id", "")),
    }
    bullets = []
    for line in hit.rationale:
        bullets.append("- " + _format_text(line, mapping))
    return "\n".join(bullets)
