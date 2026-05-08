import sys

from app.cli import main


def test_cli_show_severity_comparison_outputs_mapping_section(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "alcohol",
            "clonazepam",
            "--show-severity-comparison",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Severity Comparison" in out
    assert "shared_pd_effect_cluster: CNS_depression" in out
    assert "safety_concern_cluster: safety_concern" in out
    assert "tolerability_concern_cluster: tolerability_concern" in out
    assert "preliminary_severity: high_caution" in out
    assert "preliminary_severity: caution" in out
    assert "severity_reason: High-confidence safety concern." in out
    assert (
        "severity_reason: Multiple tolerability-related candidates identified."
        in out
    )

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out