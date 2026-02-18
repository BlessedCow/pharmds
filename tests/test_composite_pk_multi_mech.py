from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from core.constants import TRANSPORTER_PGP
from core.enums import Domain, RuleClass, Severity
from core.models import RuleHit
from rules.composite_rules import (
    apply_composites,
    apply_pk_cyp_ugt,
    apply_pk_dual_mechanism,
    apply_pk_multi_mechanism_exposure_increase,
    apply_pk_ugt_pgp,
)


@dataclass
class _FactsStub:
    pd_effects: dict
    
def _hit(
    *,
    rule_id: str,
    A: str,
    B: str,
    severity: Severity,
    rule_class: RuleClass,
    enzyme_id: str | None = None,
    transporter_id: str | None = None,
    tags: list[str] | None = None,
) -> RuleHit:
    inputs: dict[str, Any] = {"A": A, "B": B}
    if enzyme_id is not None:
        inputs["enzyme_id"] = enzyme_id
    if transporter_id is not None:
        inputs["transporter_id"] = transporter_id

    return RuleHit(
        rule_id=rule_id,
        name=rule_id,
        domain=Domain.PK,
        severity=severity,
        rule_class=rule_class,
        inputs=inputs,
        tags=tags or ["exposure_increase"],
        rationale=[],
        actions=[],
        references=[],
    )


def _find(rule_id: str, hits: list[RuleHit]) -> list[RuleHit]:
    return [h for h in hits if h.rule_id == rule_id]


def test_pk_dual_mech_cyp_pgp_emits_composite() -> None:
    # CYP + P-gp for same (A,B) should produce PK_DUAL_MECH_INCREASE
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="quetiapine",
            B="clarithromycin",
            enzyme_id="CYP3A4",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
        _hit(
            rule_id="PK_PGP_INHIB",
            A="quetiapine",
            B="clarithromycin",
            transporter_id=TRANSPORTER_PGP,
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
    ]

    out = apply_pk_dual_mechanism(cast(Any, None), base)

    comps = _find("PK_DUAL_MECH_INCREASE", out)
    assert len(comps) == 1

    c = comps[0]
    assert c.domain == Domain.PK
    assert c.inputs.get("A") == "quetiapine"
    assert c.inputs.get("B") == "clarithromycin"

    # Max severity/class from contributing hits
    assert c.severity == Severity.major
    assert c.rule_class == RuleClass.adjust_monitor

    assert "exposure_increase" in (c.tags or [])
    assert "dual_mechanism" in (c.tags or [])


def test_pk_dual_mech_requires_both_mechanisms() -> None:
    # Only CYP present -> no dual mechanism composite
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="quetiapine",
            B="clarithromycin",
            enzyme_id="CYP3A4",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
    ]

    out = apply_pk_dual_mechanism(cast(Any, None), base)
    assert _find("PK_DUAL_MECH_INCREASE", out) == []


def test_pk_cyp_ugt_wrapper_emits_cyp_ugt_composite() -> None:
    # This tests the wrapper directly (even if not enabled in apply_composites)
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="CYP3A4",
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
        _hit(
            rule_id="PK_UGT1A1_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="UGT1A1",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
    ]

    out = apply_pk_cyp_ugt(cast(Any, None), base)

    comps = _find("PK_DUAL_MECH_INCREASE_CYP_UGT", out)
    assert len(comps) == 1
    c = comps[0]

    assert c.inputs.get("A") == "drugA"
    assert c.inputs.get("B") == "drugB"
    assert c.severity == Severity.major
    assert c.rule_class == RuleClass.adjust_monitor
    assert "dual_mechanism" in (c.tags or [])


def test_pk_ugt_pgp_wrapper_emits_ugt_pgp_composite() -> None:
    base = [
        _hit(
            rule_id="PK_UGT1A1_INHIB",
            A="irinotecan",
            B="atazanavir",
            enzyme_id="UGT1A1",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
        _hit(
            rule_id="PK_PGP_INHIB",
            A="irinotecan",
            B="atazanavir",
            transporter_id=TRANSPORTER_PGP,
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
    ]

    out = apply_pk_ugt_pgp(cast(Any, None), base)

    comps = _find("PK_DUAL_MECH_INCREASE_UGT_PGP", out)
    assert len(comps) == 1
    c = comps[0]

    assert c.inputs.get("A") == "irinotecan"
    assert c.inputs.get("B") == "atazanavir"
    assert c.severity == Severity.major
    assert c.rule_class == RuleClass.adjust_monitor


def test_pk_composites_do_not_emit_without_required_tag() -> None:
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="CYP3A4",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
            tags=["something_else"],
        ),
        _hit(
            rule_id="PK_UGT1A1_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="UGT1A1",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
            tags=["something_else"],
        ),
    ]

    out = apply_pk_cyp_ugt(cast(Any, None), base)
    assert _find("PK_DUAL_MECH_INCREASE_CYP_UGT", out) == []

def test_apply_composites_idempotent_for_cyp_ugt() -> None:
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="CYP3A4",
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
        _hit(
            rule_id="PK_UGT1A1_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="UGT1A1",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
    ]

    facts = _FactsStub(pd_effects={})
    
    out1 = apply_composites(facts, base)
    out2 = apply_composites(facts, out1)

    assert len(_find("PK_DUAL_MECH_INCREASE_CYP_UGT", out1)) == 1
    assert len(_find("PK_DUAL_MECH_INCREASE_CYP_UGT", out2)) == 1
    
def test_pk_multi_mech_three_mechanisms_emits_generic_rule_id() -> None:
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="CYP3A4",
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
        _hit(
            rule_id="PK_UGT1A1_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="UGT1A1",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
        _hit(
            rule_id="PK_PGP_INHIB",
            A="drugA",
            B="drugB",
            transporter_id=TRANSPORTER_PGP,
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
    ]

    out = apply_pk_multi_mechanism_exposure_increase(cast(Any, None), base)

    comps = _find("PK_MULTI_MECH_INCREASE", out)
    assert len(comps) == 1
    c = comps[0]
    assert c.severity == Severity.major
    assert c.rule_class == RuleClass.adjust_monitor
    assert "multi_mechanism" in (c.tags or [])

def test_pk_multi_mech_idempotent() -> None:
    base = [
        _hit(
            rule_id="PK_CYP3A4_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="CYP3A4",
            severity=Severity.caution,
            rule_class=RuleClass.caution,
        ),
        _hit(
            rule_id="PK_UGT1A1_INHIB",
            A="drugA",
            B="drugB",
            enzyme_id="UGT1A1",
            severity=Severity.major,
            rule_class=RuleClass.adjust_monitor,
        ),
    ]

    out1 = apply_pk_multi_mechanism_exposure_increase(cast(Any, None), base)
    out2 = apply_pk_multi_mechanism_exposure_increase(cast(Any, None), out1)

    assert len(_find("PK_DUAL_MECH_INCREASE_CYP_UGT", out1)) == 1
    assert len(_find("PK_DUAL_MECH_INCREASE_CYP_UGT", out2)) == 1

