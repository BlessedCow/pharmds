from __future__ import annotations

from pathlib import Path

from app.cli.domains import (
    _parse_domain_selection,
    filter_rules_for_selected_domains,
)
from app.cli.pairwise import _build_reports_for_all_pairs
from rules.engine import evaluate_all, load_rules


def build_cli_pair_reports(
    args,
    *,
    facts,
    drug_ids,
    rule_dir: Path,
):
    selected = _parse_domain_selection(args.domain)

    rules_all = load_rules(rule_dir)
    rules = filter_rules_for_selected_domains(rules_all, selected)

    hits = evaluate_all(rules, facts, drug_ids)

    from rules.composite_rules import apply_composites

    hits = apply_composites(facts, hits)

    templates = {rule.id: rule.explanation_template for rule in rules}
    pair_reports = _build_reports_for_all_pairs(
        facts,
        hits,
        templates,
        drug_ids,
    )

    return selected, templates, pair_reports