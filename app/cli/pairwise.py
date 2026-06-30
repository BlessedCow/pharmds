from __future__ import annotations

from itertools import combinations

from reasoning.combine import build_pair_reports


def _build_reports_for_all_pairs(facts, hits, templates, drug_ids):
    pairs = list(combinations(drug_ids, 2))
    return build_pair_reports(
        facts=facts,
        hits=hits,
        rule_templates=templates,
        pairs=pairs,
    )