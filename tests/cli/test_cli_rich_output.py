import sys

from app.cli import main


def test_rich_details_explains_when_no_pairwise_rows(
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
            "--format",
            "rich",
            "--details",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" in out
    assert "Interaction Summary (pairwise)" in out
    assert "No pairwise rule-based rows to display." in out
    assert "Pairwise Details" in out
    assert "No pairwise detail panels to display." in out
    assert "Use --show-aggregate-summaries" in out
    assert "PK hits" not in out
    assert "PD hits" not in out


def test_rich_summary_still_renders_table_when_pairwise_rows_exist(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "warfarin",
            "fluconazole",
            "--format",
            "rich",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" in out
    assert "Interaction Summary (pairwise)" in out
    assert "PK hits" in out
    assert "PD hits" in out
    assert "No pairwise rule-based rows to display." not in out
    assert "No pairwise detail panels to display." not in out
    
def test_rich_regimen_summary_separates_regimen_flags_from_pairwise_output(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "lorazepam",
            "gabapentin",
            "trazodone",
            "--format",
            "rich",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Regimen Summary (all drugs)" in out
    assert "Regimen-wide repeated PD concern domains:" in out
    assert "Regimen-wide educational flags:" in out
    assert "Pairwise concern highlights:" in out
    assert "Interaction Summary (pairwise)" in out

    assert "Regimen-wide CNS depression concern" in out
    assert "not a diagnosis or treatment instruction" in out
    assert "Consider avoiding" not in out
    assert "intensive monitoring" not in out