from __future__ import annotations

from app.service import analyze_names

RULE_ID = "PD_ORTHOSTATIC_HYPOTENSION_ADDITIVE"


def _pd_rule_ids(
    *,
    pd_effects: list[str] | None,
) -> set[str]:
    result = analyze_names(
        ["quetiapine", "trazodone"],
        domain="all",
        pd_effects=pd_effects,
        as_json_payload=True,
    )

    assert result.ok

    return {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair["pd"]["hits"]
    }


def test_orthostatic_rule_runs_with_all_effects() -> None:
    assert RULE_ID in _pd_rule_ids(pd_effects=None)


def test_orthostatic_rule_runs_with_specific_effect_filter() -> None:
    assert RULE_ID in _pd_rule_ids(
        pd_effects=["orthostatic_hypotension"],
    )


def test_orthostatic_rule_is_removed_by_unrelated_effect_filter() -> None:
    assert RULE_ID not in _pd_rule_ids(
        pd_effects=["photosensitivity_risk"],
    )
