from __future__ import annotations

from core.enums import RuleClass, Severity


def severity_rationale(severity: Severity | str) -> str:
    value = str(getattr(severity, "value", severity))

    rationales = {
        "info": (
            "Informational because the interaction is expected to have limited "
            "clinical significance or is mainly provided for context."
        ),
        "caution": (
            "Caution because the combination may increase risk, but is often "
            "manageable with awareness, patient-specific assessment, or monitoring."
        ),
        "major": (
            "Major because the combination may produce clinically meaningful risk "
            "and should generally prompt closer monitoring, mitigation, "
            "or therapy review."
        ),
        "contraindicated": (
            "Contraindicated because the combination may create a high-risk scenario "
            "where avoidance or specialist review is generally preferred."
        ),
    }

    return rationales.get(value, "Severity rationale is not available.")


def action_rationale(rule_class: RuleClass | str) -> str:
    value = str(getattr(rule_class, "value", rule_class))

    rationales = {
        "info": (
            "Informational action because no specific therapy change is suggested "
            "from this rule alone."
        ),
        "caution": (
            "Caution action because the combination may warrant awareness, counseling, "
            "or routine monitoring depending on patient context."
        ),
        "adjust_monitor": (
            "Adjust/monitor action because the combination may require dose review, "
            "closer monitoring, timing separation, or patient-specific mitigation."
        ),
        "avoid": (
            "Avoid action because the combination may pose enough risk that an "
            "alternative, spacing strategy, or prescriber review should be considered."
        ),
    }

    return rationales.get(value, "Action rationale is not available.")