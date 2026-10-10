import sys

from app.cli import main


def test_cli_show_aggregate_evidence_outputs_summary_section(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--show-aggregate-evidence",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Evidence Summary" in out
    assert "shared_pd_effect_cluster: nausea" in out
    assert "overall_evidence_status: complete" in out
    assert "evidence_trace_count:" in out
    assert "evidence_trace_types:" in out
    assert "evidence_effect_ids: nausea" in out
    assert "evidence_statuses:" in out
    assert "evidence_gap_count:" in out
    assert "evidence_claim_count:" in out
    assert (
        "evidence_sources: 3 sources: Clarithromycin Prescribing "
        "Information (drug_label), Fluconazole Prescribing Information "
        "(drug_label), Internal curated pharmacodynamic effects dataset "
        "(internal_curated_entry)"
    ) in out
    assert "evidence_source_ids:" not in out
    assert "member_without_evidence_trace_count:" in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out


def test_cli_show_aggregate_evidence_handles_non_pd_aggregate(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "bupropion",
            "vortioxetine",
            "--show-aggregate-evidence",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Evidence Summary" in out
    assert "overall_evidence_status:" in out
    assert "evidence_trace_count:" in out
    assert "member_without_evidence_trace_count:" in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out
    
def test_cli_show_aggregate_evidence_outputs_readable_effect_labels(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "quetiapine",
            "--show-aggregate-evidence",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Evidence Summary" in out
    assert (
        "shared_pd_effect_cluster: QT_prolongation"
        " | policy_concern=safety_concern"
        " | drugs=clarithromycin, quetiapine"
        " | effect=QT_prolongation (QT prolongation)"
    ) in out
    assert "evidence_effect_ids: QT_prolongation (QT prolongation)" in out
    assert "effect_label: QT prolongation" not in out
    assert "evidence_trace_types: additive_pd_effect" in out
    assert "evidence_statuses: complete" in out
    assert "evidence_sources: none" in out
    assert (
        "evidence_sources: 2 sources: Clarithromycin Prescribing "
        "Information (drug_label), Internal curated pharmacodynamic "
        "effects dataset (internal_curated_entry)"
    ) in out
    assert "evidence_source_ids:" not in out