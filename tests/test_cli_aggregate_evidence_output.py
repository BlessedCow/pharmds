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
    assert "evidence_source_ids:" in out
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