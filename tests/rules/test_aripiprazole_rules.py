from __future__ import annotations

import pytest

from tests.rules.support import evaluate_drug_rules, rule_ids


@pytest.mark.parametrize(
    ("rule_id", "should_match"),
    (
        ("PK_CYP2D6_INHIB_SUBSTRATE", True),
        ("PK_CYP2D6_INHIB_TRAMADOL", False),
    ),
)
def test_cyp2d6_rule_selection(rule_id: str, should_match: bool) -> None:
    _, hits = evaluate_drug_rules(["aripiprazole", "fluoxetine"])
    assert (rule_id in rule_ids(hits)) is should_match
