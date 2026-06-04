import sys

from app.cli import main


def test_cli_show_aggregate_summaries_outputs_pd_summary(
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
            "--show-aggregate-summaries",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Concern Summaries" in out
    assert "shared_pd_effect_cluster: nausea" in out
    assert "drugs: clarithromycin, fluconazole" in out
    assert "effect: nausea" in out
    assert "policy_concern: tolerability_concern" in out
    assert "strongest_preliminary_severity: informational" in out
    assert "evidence_status: complete" in out
    assert "evidence_claim_count: 2" in out
    assert "evidence_source_count: 3" in out
    assert (
        "evidence_sources: 3 sources: Clarithromycin Prescribing "
        "Information (drug_label), Fluconazole Prescribing Information "
        "(drug_label), Internal curated pharmacodynamic effects dataset "
        "(internal_curated_entry)"
    ) in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out


def test_cli_show_aggregate_summaries_outputs_pk_summary(
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
            "--show-aggregate-summaries",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Concern Summaries" in out
    assert "object_exposure_increase_cluster: vortioxetine" in out
    assert "drugs: bupropion, vortioxetine" in out
    assert "effect: vortioxetine" in out
    assert "targets: CYP2D6" in out
    assert "policy_concern: mechanistic_concern" in out
    assert "strongest_preliminary_severity: informational" in out
    assert "evidence_status: not_applicable" in out
    assert "evidence_gap_count: 0" in out
    assert "evidence_claim_count: 0" in out
    assert "evidence_source_count: 0" in out
    assert "evidence_sources: none" in out

    assert "EDUCATIONAL ONLY - NOT DIAGNOSTIC" not in out
    assert "Overall: severity=" not in out
    
def test_cli_show_aggregate_summaries_respects_top_limit(
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
            "bupropion",
            "vortioxetine",
            "--show-aggregate-summaries",
            "--top",
            "1",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Concern Summaries" in out
    assert out.count("\n- ") == 1
    assert "aggregate concern" in out
    assert "hidden. Use --top 0 to show all." in out


def test_cli_show_aggregate_summaries_top_zero_shows_all(
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
            "bupropion",
            "vortioxetine",
            "--show-aggregate-summaries",
            "--top",
            "0",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Concern Summaries" in out
    assert out.count("\n- ") > 1
    assert "hidden. Use --top 0 to show all." not in out
    
def test_cli_show_aggregate_summaries_outputs_patient_risk_context(
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
            "--qt-risk",
            "--show-aggregate-summaries",
            "--top",
            "0",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "Aggregate Concern Summaries" in out
    assert "shared_pd_effect_cluster: QT_prolongation" in out
    assert "effect: QT_prolongation (QT prolongation)" in out
    assert "effect_label: QT prolongation" not in out
    assert "QT prolongation pharmacodynamic effect" in out
    assert "QT_prolongation-related pharmacodynamic effect" not in out
    assert (
        "risk_context: QT-related concern may be more important when QT risk "
        "flag is present."
    ) in out
    
def test_cli_show_aggregate_summaries_outputs_narrative(
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
            "--show-aggregate-summaries",
            "--top",
            "0",
        ],
    )

    main()

    out = capsys.readouterr().out

    assert "narrative:" in out
    assert "clarithromycin and fluconazole share a nausea-related" in out
    assert "educational and not diagnostic" in out
    assert "evidence_conflict_level: none" in out
    assert "evidence_conflict_message:" not in out
    assert "evidence_conflict_reasons: mixed source types" in out