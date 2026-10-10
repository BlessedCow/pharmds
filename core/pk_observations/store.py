"""Read source-linked PK measurements without selecting a clinical default."""

from __future__ import annotations

import sqlite3

from core.pk_observations.models import PKObservation, PKSource


def get_pk_observations(
    conn: sqlite3.Connection,
    drug_id: str,
    *,
    route: str | None = None,
    release_type: str | None = None,
) -> tuple[tuple[PKObservation, PKSource], ...]:
    """Return all matching observations with their independent sources."""
    query = (
        "SELECT o.*, s.title, s.url, s.evidence_type, s.revision_date "
        "FROM pk_observation AS o JOIN pk_source AS s ON s.id=o.source_id "
        "WHERE o.drug_id=?"
    )
    values: list[str] = [drug_id]
    if route is not None:
        query += " AND o.route=?"
        values.append(route)
    if release_type is not None:
        query += " AND o.release_type=?"
        values.append(release_type)
    query += " ORDER BY o.metric, o.id"
    rows = conn.execute(query, values).fetchall()
    return tuple(
        (
            PKObservation(
                id=row["id"],
                drug_id=row["drug_id"],
                route=row["route"],
                release_type=row["release_type"],
                metric=row["metric"],
                min_value=row["min_value"],
                max_value=row["max_value"],
                unit=row["unit"],
                population=row["population"],
                analyte=row["analyte"],
                administration_condition=row["administration_condition"],
                source_id=row["source_id"],
                dose_value=row["dose_value"],
                dose_unit=row["dose_unit"],
                notes=row["notes"],
                math_eligible=bool(row["math_eligible"]),
            ),
            PKSource(
                id=row["source_id"],
                title=row["title"],
                url=row["url"],
                evidence_type=row["evidence_type"],
                revision_date=row["revision_date"],
            ),
        )
        for row in rows
    )
