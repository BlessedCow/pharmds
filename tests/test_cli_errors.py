from __future__ import annotations

import sys

import pytest

from app.cli import DB_PATH, connect, main, resolve_drug_ids
from core.exceptions import UnknownDrugError


def test_resolve_drug_ids_raises_unknown_drug_error_for_missing_drug():
    conn = connect(DB_PATH)

    with pytest.raises(UnknownDrugError) as exc:
        resolve_drug_ids(conn, ["definitely-not-a-drug"])

    assert "definitely-not-a-drug" in exc.value.unknown


def test_resolve_drug_ids_reports_multiple_unknowns():
    conn = connect(DB_PATH)

    with pytest.raises(UnknownDrugError) as exc:
        resolve_drug_ids(conn, ["nope1", "nope2"])

    assert exc.value.unknown == ("nope1", "nope2")

def test_resolve_drug_ids_normalizes_common_alias_separators():
    conn = connect(DB_PATH)

    resolved = resolve_drug_ids(
        conn, ["wellbutrin-xl", "amphetamine dextroamphetamine"]
    )

    assert resolved == [
        "bupropion",
        "amphetamine_dextroamphetamine",
    ]


def test_resolve_drug_ids_preserves_input_order_after_alias_resolution():
    conn = connect(DB_PATH)

    assert resolve_drug_ids(conn, ["diflucan", "biaxin", "seroquel"]) == [
        "fluconazole",
        "clarithromycin",
        "quetiapine",
    ]
    
def test_resolve_drug_ids_deduplicates_after_alias_resolution():
    conn = connect(DB_PATH)

    assert resolve_drug_ids(
        conn,
        ["wellbutrin-xl", "bupropion", "diflucan", "fluconazole"],
    ) == [
        "bupropion",
        "fluconazole",
    ]

def test_resolve_drug_ids_includes_practical_recovery_medication_aliases():
    conn = connect(DB_PATH)

    assert resolve_drug_ids(conn, ["sublocade", "kloxxado", "depade"]) == [
        "buprenorphine",
        "naloxone",
        "naltrexone",
    ]


def test_resolve_drug_ids_includes_mecamylamine_brand_alias():
    conn = connect(DB_PATH)

    assert resolve_drug_ids(conn, ["inversine", "chantix"]) == [
        "mecamylamine",
        "varenicline",
    ]
    
def test_cli_unknown_drug_message_includes_suggestions(capsys, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["pharmds", "quetiaipne", "fluconazole"],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    err = capsys.readouterr().err
    assert exc.value.code == 2
    assert "Drug 'quetiaipne' was not found. Did you mean: quetiapine" in err


def test_cli_unknown_drug_message_without_suggestions_is_actionable(
    capsys,
    monkeypatch,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["pharmds", "xqznotadrug", "fluconazole"],
    )

    with pytest.raises(SystemExit) as exc:
        main()

    err = capsys.readouterr().err
    assert exc.value.code == 2
    assert (
        "Drug 'xqznotadrug' was not found. Check the spelling, or try a "
        "generic name or known brand name."
    ) in err
    assert "common separators" in err    