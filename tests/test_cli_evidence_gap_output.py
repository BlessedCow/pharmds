import sys

from app.cli import main


def test_cli_show_evidence_gaps_outputs_grouped_report(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--show-evidence-gaps",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "PD Effect Evidence Gaps" in out
    assert "Total PD effects checked:" in out
    assert "Missing/partial evidence rows:" in out
    assert "Grouped by PD effect:" in out
    assert "Grouped by drug:" in out
    assert "Grouped by source type:" in out
    assert "Backfill planning report:" in out

def test_cli_show_evidence_gaps_outputs_backfill_plan_sections(
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
            "--show-evidence-gaps",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Backfill planning report:" in out
    assert (
        "No backfill tasks found." in out
        or "Prioritized tasks:" in out
    )

def test_cli_show_evidence_gaps_can_include_complete_rows(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "fluconazole",
            "--show-evidence-gaps",
            "--show-complete-evidence-coverage",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Complete/moderate/high rows:" in out
    assert "source_types=" in out