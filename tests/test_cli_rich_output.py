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