from __future__ import annotations

from collections.abc import Sequence

from app.cli import RULE_DIR
from core.models import Facts, RuleHit
from rules.engine import evaluate_all, load_rules
from tests.mechanisms.support import load_drug_facts


def evaluate_drug_rules(drug_names: Sequence[str]) -> tuple[Facts, list[RuleHit]]:
    """Evaluate curated rule findings using independently loaded drug facts."""
    drug_ids, facts = load_drug_facts(drug_names)
    hits = evaluate_all(load_rules(RULE_DIR), facts, drug_ids)
    return facts, hits


def rule_ids(hits: Sequence[RuleHit]) -> set[str]:
    """Return the unique identifiers present in a collection of rule hits."""
    return {hit.rule_id for hit in hits}
