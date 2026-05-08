import sys

from app.cli import main


def test_cli_show_severity_outputs_debug_section(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["pharmds", "alcohol", "clonazepam", "--show-severity"],
    )

    main()

    out = capsys.readouterr().out

    assert "Severity Annotations" in out
    assert "alcohol + clonazepam" in out
    assert "effect=CNS_depression" in out
    assert "preliminary_severity:" in out
    assert "severity_reason:" in out
    assert "related_effects:" in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out