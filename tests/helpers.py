from __future__ import annotations

from typing import Iterable
from core.models import RuleHit


def rule_ids(hits: Iterable[RuleHit]) -> set[str]:
    """Return all rule_ids from a list of RuleHit objects."""
    return {h.rule_id for h in hits}


def assert_no_hits(hits: Iterable[RuleHit]) -> None:
    """Assert that no rules fired."""
    assert list(hits) == [], f"Expected no rule hits, but got: {rule_ids(hits)}"


def assert_has_rule(hits: Iterable[RuleHit], rule_id: str) -> None:
    """Assert that a specific rule fired."""
    rids = rule_ids(hits)
    assert rule_id in rids, f"Expected rule '{rule_id}' to fire, got: {rids}"


def assert_no_rule(hits: Iterable[RuleHit], rule_id: str) -> None:
    """Assert that a specific rule did NOT fire."""
    rids = rule_ids(hits)
    assert rule_id not in rids, f"Did NOT expect rule '{rule_id}', but got: {rids}"
