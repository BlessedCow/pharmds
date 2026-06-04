import sys

from app.cli import main


def test_default_plain_output_includes_public_result_summaries(
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
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" in out
    assert "Key Interaction Summaries" in out
    assert "Shared QT prolongation concern" in out
    assert "Shared nausea concern" in out
    assert "concern_type:" in out
    assert "severity:" in out
    assert "evidence:" in out
    assert "explanation:" in out

    assert "No rule-based interactions detected" not in out

def test_default_plain_output_public_summaries_respect_top_limit(
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
            "--top",
            "1",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Key Interaction Summaries" in out
    assert out.count("\n- Shared ") == 1
    assert "key interaction" in out
    assert "hidden. Use --top 0 to show all." in out
    assert "No rule-based interactions detected" not in out


def test_default_plain_output_top_zero_shows_all_public_summaries(
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
            "--top",
            "0",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Key Interaction Summaries" in out
    assert out.count("\n- Shared ") > 1
    assert "hidden. Use --top 0 to show all." not in out
    
def test_default_plain_output_does_not_show_clopidogrel_rule_without_clopidogrel(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "citalopram",
            "fluconazole",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "clopidogrel" not in out.lower()
    assert "CYP2C19 inhibition can reduce activation of clopidogrel" not in out
    
def test_default_plain_output_includes_regimen_summary_for_three_drugs(
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
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" in out
    assert "Regimen Summary" in out
    assert "overview:" in out
    assert "pairwise_section:" in out
    assert "regimen_wide_section:" in out
    assert "Regimen-wide repeated PD concern domains:" in out
    assert "Regimen-wide educational flags:" in out
    assert "Pairwise concern highlights:" in out
    assert "Regimen-wide CNS depression concern" in out
    assert "not a diagnosis or treatment instruction" in out
    assert "Consider avoiding" not in out
    assert "intensive monitoring" not in out