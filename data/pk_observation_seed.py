"""Insert curated PK measurements without replacing parent drug rows."""

from __future__ import annotations

import sqlite3

from core.pk_observations.models import PKObservation, PKSource


def upsert_pk_observations(
    conn: sqlite3.Connection,
    sources: tuple[PKSource, ...],
    observations: tuple[PKObservation, ...],
) -> None:
    for source in sources:
        conn.execute(
            "INSERT INTO pk_source(id,title,url,evidence_type,revision_date) "
            "VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
            "title=excluded.title,url=excluded.url,"
            "evidence_type=excluded.evidence_type,revision_date=excluded.revision_date",
            (
                source.id,
                source.title,
                source.url,
                source.evidence_type,
                source.revision_date,
            ),
        )
    for observation in observations:
        conn.execute(
            "INSERT INTO pk_observation("
            "id,drug_id,route,release_type,metric,min_value,max_value,unit,"
            "population,analyte,administration_condition,source_id,dose_value,"
            "dose_unit,notes,math_eligible) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET drug_id=excluded.drug_id,"
            "route=excluded.route,release_type=excluded.release_type,"
            "metric=excluded.metric,min_value=excluded.min_value,"
            "max_value=excluded.max_value,unit=excluded.unit,"
            "population=excluded.population,analyte=excluded.analyte,"
            "administration_condition=excluded.administration_condition,"
            "source_id=excluded.source_id,dose_value=excluded.dose_value,"
            "dose_unit=excluded.dose_unit,notes=excluded.notes,"
            "math_eligible=excluded.math_eligible",
            (
                observation.id,
                observation.drug_id,
                observation.route,
                observation.release_type,
                observation.metric,
                observation.min_value,
                observation.max_value,
                observation.unit,
                observation.population,
                observation.analyte,
                observation.administration_condition,
                observation.source_id,
                observation.dose_value,
                observation.dose_unit,
                observation.notes,
                int(observation.math_eligible),
            ),
        )
