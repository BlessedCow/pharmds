from __future__ import annotations

import pytest

from tests.rules.support import evaluate_drug_rules, rule_ids


@pytest.mark.parametrize(
    ("drug_names", "expected_rule_id"),
    [
        pytest.param(
            ("warfarin", "fluconazole"),
            "PK_CYP2C9_INHIB_WARFARIN",
            id="warfarin-fluconazole-cyp2c9",
        ),
        pytest.param(
            ("citalopram", "ondansetron"),
            "PD_QT_ADDITIVE",
            id="citalopram-ondansetron-qt",
        ),
    ],
)
def test_curated_interaction_scenarios(
    drug_names: tuple[str, str], expected_rule_id: str
) -> None:
    _, hits = evaluate_drug_rules(drug_names)
    assert expected_rule_id in rule_ids(hits)
