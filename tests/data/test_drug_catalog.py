from __future__ import annotations

import sqlite3

from data.drug_catalog import (
    get_drug_catalog_entry,
    list_drug_catalog,
)


def _build_catalog_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.executescript("""
        CREATE TABLE drug (
            id TEXT PRIMARY KEY,
            generic_name TEXT NOT NULL,
            drug_class TEXT
        );

        CREATE TABLE drug_alias (
            drug_id TEXT NOT NULL,
            alias TEXT NOT NULL
        );

        CREATE TABLE drug_release_type (
            drug_id TEXT NOT NULL,
            release_type TEXT NOT NULL
        );
        
        CREATE TABLE drug_formulation (
            drug_id TEXT NOT NULL,
            route TEXT NOT NULL,
            release_type TEXT NOT NULL
        );
        """)

    conn.executemany(
        """
        INSERT INTO drug(id, generic_name, drug_class)
        VALUES(?, ?, ?)
        """,
        [
            ("venlafaxine", "venlafaxine", "SNRI"),
            ("vortioxetine", "vortioxetine", "serotonin modulator"),
            ("uncurated", "uncurated", None),
        ],
    )

    conn.executemany(
        """
        INSERT INTO drug_alias(drug_id, alias)
        VALUES(?, ?)
        """,
        [
            ("venlafaxine", "effexor"),
            ("venlafaxine", "effexor xr"),
            ("vortioxetine", "trintellix"),
        ],
    )

    conn.executemany(
        """
        INSERT INTO drug_release_type(drug_id, release_type)
        VALUES(?, ?)
        """,
        [
            ("venlafaxine", "ir"),
            ("venlafaxine", "er"),
            ("vortioxetine", "ir"),
        ],
    )

    conn.executemany(
        """
        INSERT INTO drug_formulation(
            drug_id,
            route,
            release_type
        )
        VALUES(?, ?, ?)
        """,
        [
            ("venlafaxine", "oral", "ir"),
            ("venlafaxine", "oral", "er"),
            ("vortioxetine", "oral", "ir"),
        ],
    )

    return conn


def test_list_drug_catalog_returns_sorted_entries():
    conn = _build_catalog_connection()

    entries = list_drug_catalog(conn)

    assert [entry.id for entry in entries] == [
        "uncurated",
        "venlafaxine",
        "vortioxetine",
    ]


def test_list_drug_catalog_includes_aliases_and_release_types():
    conn = _build_catalog_connection()

    entries = {entry.id: entry for entry in list_drug_catalog(conn)}

    venlafaxine = entries["venlafaxine"]

    assert venlafaxine.generic_name == "venlafaxine"
    assert venlafaxine.drug_class == "SNRI"
    assert venlafaxine.aliases == (
        "effexor",
        "effexor xr",
    )
    assert venlafaxine.release_types == (
        "er",
        "ir",
    )


def test_list_drug_catalog_uses_unknown_release_type_fallback():
    conn = _build_catalog_connection()

    entries = {entry.id: entry for entry in list_drug_catalog(conn)}

    assert entries["uncurated"].release_types == ("unknown",)


def test_get_drug_catalog_entry_returns_single_drug():
    conn = _build_catalog_connection()

    entry = get_drug_catalog_entry(
        conn,
        "vortioxetine",
    )

    assert entry is not None
    assert entry.id == "vortioxetine"
    assert entry.generic_name == "vortioxetine"
    assert entry.aliases == ("trintellix",)
    assert entry.release_types == ("ir",)
    assert len(entry.formulations) == 1
    assert entry.formulations[0].route == "oral"
    assert entry.formulations[0].release_types == ("ir",)


def test_get_drug_catalog_entry_returns_none_for_unknown_drug():
    conn = _build_catalog_connection()

    entry = get_drug_catalog_entry(
        conn,
        "does-not-exist",
    )

    assert entry is None


def test_list_drug_catalog_includes_formulations():
    conn = _build_catalog_connection()

    entries = {entry.id: entry for entry in list_drug_catalog(conn)}

    venlafaxine = entries["venlafaxine"]

    assert len(venlafaxine.formulations) == 1

    formulation = venlafaxine.formulations[0]

    assert formulation.route == "oral"
    assert formulation.release_types == (
        "er",
        "ir",
    )
