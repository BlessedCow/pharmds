from itertools import combinations

from reasoning.combine import build_pair_reports
from tests.test_golden_scenarios import _run


def test_polypharmacy_generates_multiple_pair_reports():
    facts, hits = _run(["digoxin", "verapamil", "clarithromycin"])
    templates = {}  # fine for this test

    pairs = list(combinations(["digoxin", "verapamil", "clarithromycin"], 2))
    reports = build_pair_reports(facts, hits, templates, pairs=pairs)

    # Expect at least the digoxin+verapamil report to exist (it should in your ruleset)
    assert len(reports) >= 2
