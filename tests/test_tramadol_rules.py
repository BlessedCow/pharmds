from __future__ import annotations

from tests.test_golden_scenarios import _run


def test_tramadol_fluoxetine_hits_tramadol_specific_cyp2d6_rule():
    _, hits = _run(["tramadol", "fluoxetine"])
    assert any(h.rule_id == "PK_CYP2D6_INHIB_TRAMADOL" for h in hits)


def test_tramadol_fluoxetine_does_not_hit_generic_cyp2d6_substrate_rule():
    _, hits = _run(["tramadol", "fluoxetine"])
    assert not any(h.rule_id == "PK_CYP2D6_INHIB_SUBSTRATE" for h in hits)