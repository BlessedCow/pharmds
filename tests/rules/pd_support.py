from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from app.service import analyze_names


def pairwise_rule_ids(
    drug_names: Sequence[str],
    *,
    domain: Literal["all", "pk", "pd"] = "all",
    finding_domain: Literal["pk", "pd"] = "pd",
    pd_effects: list[str] | None = None,
) -> set[str]:
    """Collect rule IDs from one domain of the validated pairwise result."""
    result = analyze_names(
        list(drug_names),
        domain=domain,
        pd_effects=pd_effects,
        as_json_payload=True,
    )
    assert result.ok
    return {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair[finding_domain]["hits"]
    }


def pd_rule_ids(
    drug_names: Sequence[str],
    *,
    pd_effects: list[str] | None = None,
) -> set[str]:
    """Return PD rule identifiers from the public JSON analysis result."""
    return pairwise_rule_ids(drug_names, pd_effects=pd_effects)
