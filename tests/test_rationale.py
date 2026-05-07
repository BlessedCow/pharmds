from __future__ import annotations

from core.enums import RuleClass, Severity
from reasoning.rationale import action_rationale, severity_rationale


def test_severity_rationale_accepts_enums_and_strings() -> None:
    assert "clinically meaningful" in severity_rationale(Severity.major)
    assert "high-risk" in severity_rationale("contraindicated")


def test_action_rationale_accepts_enums_and_strings() -> None:
    assert "dose review" in action_rationale(RuleClass.adjust_monitor)
    assert "alternative" in action_rationale("avoid")


def test_unknown_values_return_fallback() -> None:
    assert severity_rationale("unexpected") == "Severity rationale is not available."
    assert action_rationale("unexpected") == "Action rationale is not available."