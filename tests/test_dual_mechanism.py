from __future__ import annotations

from core.enums import Domain, RuleClass, Severity
from core.models import Facts, RuleHit
from rules.composite_rules import apply_pk_dual_mechanism


def test_dual_mechanism_increase_adds_composite_hit_and_uses_max_severity():
    facts = Facts()

    # CYP exposure increase hit (enzyme_id present)
    h1 = RuleHit(
        rule_id="PK_CYP3A4_STRONG_INHIB",
        name="CYP inhibition increases exposure",
        domain=Domain.PK,
        severity=Severity.major,
        rule_class=RuleClass.adjust_monitor,
        inputs={"A": "tacrolimus", "B": "clarithromycin", "enzyme_id": "CYP3A4"},
        tags=["exposure_increase"],
        rationale=[],
        actions=[],
        references=[],
    )

    # P-gp exposure increase hit (transporter_id == P-gp)
    h2 = RuleHit(
        rule_id="PK_PGP_INHIB_TACROLIMUS",
        name="P-gp inhibition increases exposure",
        domain=Domain.PK,
        severity=Severity.caution,
        rule_class=RuleClass.caution,
        inputs={"A": "tacrolimus", "B": "clarithromycin", "transporter_id": "P-gp"},
        tags=["exposure_increase"],
        rationale=[],
        actions=[],
        references=[],
    )

    out = apply_pk_dual_mechanism(facts, [h1, h2])

    dual = [h for h in out if h.rule_id == "PK_DUAL_MECH_INCREASE"]
    assert len(dual) == 1

    dh = dual[0]
    assert dh.domain == Domain.PK
    assert dh.inputs["A"] == "tacrolimus"
    assert dh.inputs["B"] == "clarithromycin"

    # Option B: max severity/class among contributing increase hits
    assert dh.severity == Severity.major
    assert dh.rule_class == RuleClass.adjust_monitor
    assert "dual_mechanism" in (dh.tags or [])
