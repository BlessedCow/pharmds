from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.pk_observations.store import get_pk_observations
from data.curation.pk_observations import load_pk_curation
from data.migrate_pk_observations import migrate
from data.seed_sqlite import apply_schema, connect, seed


def _payload() -> dict:
    return {
        "version": 1,
        "sources": [
            {
                "id": "label-example",
                "title": "Example prescribing label",
                "url": "https://example.org/label",
                "evidence_type": "prescribing_label",
                "revision_date": "2026-01-01",
            }
        ],
        "observations": [
            {
                "id": "midazolam-tmax-example",
                "drug_id": "midazolam",
                "route": "oral",
                "release_type": "ir",
                "metric": "tmax",
                "min_value": 1,
                "max_value": 2,
                "unit": "hours",
                "population": "Example healthy adult study population",
                "analyte": "midazolam",
                "administration_condition": "fasted",
                "source_id": "label-example",
                "dose_value": 10,
                "dose_unit": "mg",
            }
        ],
    }


def _write(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "pk_observations.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_sourced_observation_seeds_and_reads_with_formulation_filter(
    tmp_path: Path,
) -> None:
    path = _write(tmp_path, _payload())
    sources, observations = load_pk_curation(path)
    assert sources[0].id == observations[0].source_id
    db = connect(tmp_path / "pharmds.sqlite3")
    try:
        apply_schema(db)
        seed(db, pk_curation_path=path)
        db.commit()
        found = get_pk_observations(db, "midazolam", route="oral", release_type="ir")
        assert found == ((observations[0], sources[0]),)
        assert get_pk_observations(db, "midazolam", route="iv") == ()
        assert get_pk_observations(db, "rifampin") == ()
        apply_schema(db)
        seed(db, pk_curation_path=path)
        assert len(get_pk_observations(db, "midazolam")) == 1
    finally:
        db.close()


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("route", "topical", "curated formulation"),
        ("release_type", "er", "curated formulation"),
        ("source_id", "unknown", "unknown source"),
        ("unit", "days", "metric or unit"),
        ("min_value", -1, "nonnegative"),
        ("min_value", float("nan"), "finite"),
        ("max_value", 0.5, "range"),
        ("population", "", "nonempty"),
    ],
)
def test_rejects_invalid_observation(
    tmp_path: Path, field: str, value: object, error: str
) -> None:
    payload = _payload()
    payload["observations"][0][field] = value
    with pytest.raises(ValueError, match=error):
        load_pk_curation(_write(tmp_path, payload))


def test_concentration_and_auc_require_a_measured_dose(tmp_path: Path) -> None:
    for metric, unit in (("cmax", "ng/mL"), ("auc", "ng*h/mL")):
        payload = _payload()
        observation = payload["observations"][0]
        observation.update(metric=metric, unit=unit)
        del observation["dose_value"]
        del observation["dose_unit"]
        with pytest.raises(ValueError, match="measured dose"):
            load_pk_curation(_write(tmp_path, payload))


def test_bioavailability_is_fraction_bounded_by_one(tmp_path: Path) -> None:
    payload = _payload()
    payload["observations"][0].update(
        metric="bioavailability", unit="fraction", min_value=0.2, max_value=1.1
    )
    with pytest.raises(ValueError, match="range"):
        load_pk_curation(_write(tmp_path, payload))


def test_duplicate_ids_and_invalid_sources_are_rejected(tmp_path: Path) -> None:
    payload = _payload()
    payload["observations"].append(copy.deepcopy(payload["observations"][0]))
    with pytest.raises(ValueError, match="Duplicate PK observation"):
        load_pk_curation(_write(tmp_path, payload))

    payload = _payload()
    payload["sources"][0]["url"] = "http://example.org/label"
    with pytest.raises(ValueError, match="HTTPS"):
        load_pk_curation(_write(tmp_path, payload))

    payload = _payload()
    payload["sources"][0]["revision_date"] = "2026-13-01"
    with pytest.raises(ValueError, match="ISO date"):
        load_pk_curation(_write(tmp_path, payload))


def test_default_curation_preserves_drugs_and_inserts_sourced_claims(
    tmp_path: Path,
) -> None:
    sources, observations = load_pk_curation()
    assert len(sources) == 75
    assert len(observations) == 185
    assert len({observation.drug_id for observation in observations}) == 74
    assert all(observation.source_id in {source.id for source in sources}
               for observation in observations)
    db = connect(tmp_path / "empty.sqlite3")
    try:
        apply_schema(db)
        seed(db)
        assert db.execute("SELECT count(*) FROM drug").fetchone()[0] > 0
        assert db.execute("SELECT count(*) FROM pk_observation").fetchone()[0] == 185
        assert len(get_pk_observations(db, "vortioxetine", route="oral",
                                       release_type="ir")) == 3
        assert get_pk_observations(db, "bupropion", release_type="sr") == ()
        assert len(get_pk_observations(db, "atomoxetine")) == 6
    finally:
        db.close()


def test_calculation_flag_requires_a_point_half_life(tmp_path: Path) -> None:
    payload = _payload()
    payload["observations"][0]["math_eligible"] = True
    with pytest.raises(ValueError, match="single positive half-life"):
        load_pk_curation(_write(tmp_path, payload))
    payload["observations"][0]["math_eligible"] = "true"
    with pytest.raises(ValueError, match="must be boolean"):
        load_pk_curation(_write(tmp_path, payload))


def test_migration_adds_math_flag_to_previous_database_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from data import seed_sqlite

    current_schema = seed_sqlite.SCHEMA_PATH.read_text(encoding="utf-8")
    old_schema = current_schema.replace(
        "  math_eligible INTEGER NOT NULL DEFAULT 0 CHECK (math_eligible IN (0, 1)),\n",
        "",
    )
    assert old_schema != current_schema
    schema_path = tmp_path / "old_schema.sql"
    schema_path.write_text(old_schema, encoding="utf-8")
    db = connect(tmp_path / "old.sqlite3")
    try:
        monkeypatch.setattr(seed_sqlite, "SCHEMA_PATH", schema_path)
        apply_schema(db)
        empty = _write(tmp_path, {"version": 1, "sources": [], "observations": []})
        seed(db, pk_curation_path=empty)
        db.execute("UPDATE drug SET notes='retained' WHERE id='vortioxetine'")
        db.commit()
        original_schema_path = (
            Path(__file__).resolve().parents[2] / "data" / "schema.sql"
        )
        monkeypatch.setattr(seed_sqlite, "SCHEMA_PATH", original_schema_path)
        migrate(db)
        assert len(get_pk_observations(db, "vortioxetine")) == 3
        flags = {
            observation.id: observation.math_eligible
            for observation, _ in get_pk_observations(db, "vortioxetine")
        }
        assert flags["trintellix-parent-terminal-half-life"] is True
        assert db.execute(
            "SELECT notes FROM drug WHERE id='vortioxetine'"
        ).fetchone()[0] == "retained"
    finally:
        db.close()


def test_existing_database_migration_preserves_other_data_and_updates_source(
    tmp_path: Path,
) -> None:
    db = connect(tmp_path / "existing.sqlite3")
    try:
        apply_schema(db)
        seed(db)
        db.execute("UPDATE drug SET notes=? WHERE id=?", ("local note", "midazolam"))
        db.commit()
        payload = _payload()
        path = _write(tmp_path, payload)
        migrate(db, curation_path=path)
        payload["sources"][0]["title"] = "Revised source title"
        migrate(db, curation_path=_write(tmp_path, payload))
        found = get_pk_observations(db, "midazolam", route="oral")
        assert len(found) == 1
        assert found[0][1].title == "Revised source title"
        assert db.execute(
            "SELECT notes FROM drug WHERE id='midazolam'"
        ).fetchone()[0] == "local note"
    finally:
        db.close()
