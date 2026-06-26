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

    assert "alcohol + clonazepam" in out
    assert "effect=CNS_depression" in out
    assert "preliminary_severity:" in out
    assert "severity_reason:" in out
    assert "related_effects:" in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out


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

    assert "Pairwise Migration Debug: Severity Comparison" in out
    assert "shared_pd_effect_cluster: CNS_depression" in out
    assert "safety_concern_cluster: safety_concern" in out
    assert "tolerability_concern_cluster: tolerability_concern" in out
    assert "strongest_preliminary_severity: high_caution" in out
    assert "strongest_preliminary_severity: caution" in out
    assert "contributing_preliminary_severities: high_caution" in out
    assert "contributing_preliminary_severities: caution" in out
    assert "severity_reason: High-confidence safety concern." in out
    assert (
        "severity_reason: Multiple tolerability-related candidates identified."
        in out
    )

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out
    
def test_cli_show_pairwise_migration_debug_labels_old_and_mechanism_outputs(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "pharmds",
            "clarithromycin",
            "ondansetron",
            "--show-pairwise-migration-debug",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Pairwise Migration Debug" in out
    assert "Old Pairwise Rule Pipeline: Rule Reports" in out
    assert "Mechanism Pipeline: Pairwise Adapter Concerns" in out
    assert "rules=PD_QT_ADDITIVE" in out
    assert "concern=QT_prolongation" in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Key Interaction Summaries" not in out