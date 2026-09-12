from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class DrugFormulation:
    route: str
    release_types: tuple[str, ...]


@dataclass(frozen=True)
class DrugCatalogEntry:
    id: str
    generic_name: str
    drug_class: str | None
    aliases: tuple[str, ...]
    release_types: tuple[str, ...]
    formulations: tuple[DrugFormulation, ...]


def list_drug_catalog(
    conn: sqlite3.Connection,
) -> tuple[DrugCatalogEntry, ...]:
    rows = conn.execute("""
        SELECT
            id,
            generic_name,
            drug_class
        FROM drug
        ORDER BY generic_name COLLATE NOCASE, id
        """).fetchall()

    aliases_by_drug = _load_aliases(conn)
    release_types_by_drug = _load_release_types(conn)
    formulations_by_drug = _load_formulations(conn)

    return tuple(
        DrugCatalogEntry(
            id=row["id"],
            generic_name=row["generic_name"],
            drug_class=row["drug_class"],
            aliases=aliases_by_drug.get(row["id"], ()),
            release_types=release_types_by_drug.get(
                row["id"],
                ("unknown",),
            ),
            formulations=formulations_by_drug.get(
                row["id"],
                (),
            ),
        )
        for row in rows
    )


def get_drug_catalog_entry(
    conn: sqlite3.Connection,
    drug_id: str,
) -> DrugCatalogEntry | None:
    row = conn.execute(
        """
        SELECT
            id,
            generic_name,
            drug_class
        FROM drug
        WHERE id = ?
        """,
        (drug_id,),
    ).fetchone()

    if row is None:
        return None

    aliases = tuple(
        alias_row["alias"]
        for alias_row in conn.execute(
            """
            SELECT alias
            FROM drug_alias
            WHERE drug_id = ?
            ORDER BY alias COLLATE NOCASE
            """,
            (drug_id,),
        ).fetchall()
    )

    release_types = tuple(
        release_row["release_type"]
        for release_row in conn.execute(
            """
            SELECT release_type
            FROM drug_release_type
            WHERE drug_id = ?
            ORDER BY release_type COLLATE NOCASE
            """,
            (drug_id,),
        ).fetchall()
    )

    if not release_types:
        release_types = ("unknown",)

    formulations = _load_formulations_for_drug(
        conn,
        drug_id,
    )

    return DrugCatalogEntry(
        id=row["id"],
        generic_name=row["generic_name"],
        drug_class=row["drug_class"],
        aliases=aliases,
        release_types=release_types,
        formulations=formulations,
    )


def _load_aliases(
    conn: sqlite3.Connection,
) -> dict[str, tuple[str, ...]]:
    rows = conn.execute("""
        SELECT
            drug_id,
            alias
        FROM drug_alias
        ORDER BY drug_id, alias COLLATE NOCASE
        """).fetchall()

    collected: dict[str, list[str]] = {}

    for row in rows:
        collected.setdefault(row["drug_id"], []).append(row["alias"])

    return {drug_id: tuple(aliases) for drug_id, aliases in collected.items()}


def _load_release_types(
    conn: sqlite3.Connection,
) -> dict[str, tuple[str, ...]]:
    rows = conn.execute("""
        SELECT
            drug_id,
            release_type
        FROM drug_release_type
        ORDER BY drug_id, release_type COLLATE NOCASE
        """).fetchall()

    collected: dict[str, list[str]] = {}

    for row in rows:
        collected.setdefault(row["drug_id"], []).append(row["release_type"])

    return {
        drug_id: tuple(release_types) for drug_id, release_types in collected.items()
    }


def _load_formulations(
    conn: sqlite3.Connection,
) -> dict[str, tuple[DrugFormulation, ...]]:
    rows = conn.execute("""
        SELECT
            drug_id,
            route,
            release_type
        FROM drug_formulation
        ORDER BY
            drug_id,
            route COLLATE NOCASE,
            release_type COLLATE NOCASE
        """).fetchall()

    collected: dict[str, dict[str, list[str]]] = {}

    for row in rows:
        drug_routes = collected.setdefault(
            row["drug_id"],
            {},
        )
        drug_routes.setdefault(
            row["route"],
            [],
        ).append(row["release_type"])

    return {
        drug_id: tuple(
            DrugFormulation(
                route=route,
                release_types=tuple(release_types),
            )
            for route, release_types in routes.items()
        )
        for drug_id, routes in collected.items()
    }


def _load_formulations_for_drug(
    conn: sqlite3.Connection,
    drug_id: str,
) -> tuple[DrugFormulation, ...]:
    rows = conn.execute(
        """
        SELECT
            route,
            release_type
        FROM drug_formulation
        WHERE drug_id = ?
        ORDER BY
            route COLLATE NOCASE,
            release_type COLLATE NOCASE
        """,
        (drug_id,),
    ).fetchall()

    collected: dict[str, list[str]] = {}

    for row in rows:
        collected.setdefault(
            row["route"],
            [],
        ).append(row["release_type"])

    return tuple(
        DrugFormulation(
            route=route,
            release_types=tuple(release_types),
        )
        for route, release_types in collected.items()
    )
