from __future__ import annotations

from tests.test_golden_scenarios import _run


def test_aripiprazole_fluoxetine_hits_generic_cyp2d6_inhibition():
    _, hits = _run(["aripiprazole", "fluoxetine"])
    assert any(h.rule_id == "PK_CYP2D6_INHIB_SUBSTRATE" for h in hits)


def test_aripiprazole_fluoxetine_does_not_hit_tramadol_rule():
    _, hits = _run(["aripiprazole", "fluoxetine"])
    assert not any(h.rule_id == "PK_CYP2D6_INHIB_TRAMADOL" for h in hits)