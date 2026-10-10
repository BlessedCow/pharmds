from __future__ import annotations

from tests.rules.pd_support import pd_rule_ids

RULE_ID = "PD_ORTHOSTATIC_HYPOTENSION_ADDITIVE"


def test_orthostatic_rule_runs_with_all_effects() -> None:
    assert RULE_ID in pd_rule_ids(("quetiapine", "trazodone"), pd_effects=None)

def test_orthostatic_rule_runs_with_specific_effect_filter() -> None:
    assert RULE_ID in pd_rule_ids(
        ("quetiapine", "trazodone"),
        pd_effects=["orthostatic_hypotension"],
    )

def test_orthostatic_rule_is_removed_by_unrelated_effect_filter() -> None:
    assert RULE_ID not in pd_rule_ids(
        ("quetiapine", "trazodone"),
        pd_effects=["photosensitivity_risk"],
    )
