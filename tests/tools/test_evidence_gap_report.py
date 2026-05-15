from tools.evidence_gap_report import (
    approved_active_pd_effect_claim_pairs,
    build_report_lines,
    curated_pd_effect_pairs,
    missing_pd_effect_claim_pairs,
)


def test_curated_pd_effect_pairs_returns_known_pairs():
    pairs = curated_pd_effect_pairs()

    assert ("clarithromycin", "nausea") in pairs
    assert ("fluconazole", "QT_prolongation") in pairs


def test_approved_active_pd_effect_claim_pairs_returns_known_pairs():
    pairs = approved_active_pd_effect_claim_pairs()

    assert ("clarithromycin", "nausea") in pairs
    assert ("fluconazole", "QT_prolongation") in pairs


def test_missing_pd_effect_claim_pairs_returns_no_current_gaps():
    assert missing_pd_effect_claim_pairs() == []


def test_build_report_lines_returns_no_gap_report():
    assert build_report_lines() == [
        "Evidence gap report",
        "",
        "PD effects without approved active evidence claims:",
        "- None",
    ]