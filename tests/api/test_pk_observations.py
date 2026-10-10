from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from api.routes import drugs
from data.seed_sqlite import apply_schema, connect, seed


@pytest.fixture
def pk_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "catalog.sqlite3"
    conn = connect(path)
    try:
        apply_schema(conn)
        seed(conn)
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(drugs, "DB_PATH", path)
    return path


def test_observation_endpoint_preserves_formulation_and_source(pk_db: Path) -> None:
    result = drugs.get_drug_pk_observations(
        "VORTIOXETINE", route="oral", release_type="ir"
    )
    assert result.drug_id == "vortioxetine"
    assert len(result.observations) == 3
    assert all(row.source.url.startswith("https://dailymed.nlm.nih.gov/")
               for row in result.observations)
    assert drugs.get_drug_pk_observations(
        "bupropion", route="oral", release_type="sr"
    ).observations == []


def test_observation_endpoint_distinguishes_unknown_drug(pk_db: Path) -> None:
    with pytest.raises(HTTPException) as exc:
        drugs.get_drug_pk_observations("not-in-catalog")
    assert exc.value.status_code == 404


def test_math_endpoint_retains_source_and_limits(pk_db: Path) -> None:
    result = drugs.get_drug_pk_observation_math(
        "vortioxetine", "trintellix-parent-terminal-half-life", 66
    )
    assert result.observation.notes is not None
    assert len(result.traces) == 2
    assert result.traces[0].result == pytest.approx(0.5)
    assert result.traces[1].result == pytest.approx(0.5)
    assert all(trace.source_ids == ["dailymed-trintellix-v21"]
               for trace in result.traces)
    assert all(trace.assumptions and trace.limitations for trace in result.traces)


@pytest.mark.parametrize(
    "drug_id,observation_id,status",
    [
        ("vortioxetine", "trintellix-parent-tmax", 422),
        ("vortioxetine", "missing", 404),
        ("bupropion", "trintellix-parent-terminal-half-life", 404),
        ("paroxetine", "paroxetine-ir-half_life-1", 422),
    ],
)
def test_math_rejects_inapplicable_observations(
    pk_db: Path, drug_id: str, observation_id: str, status: int
) -> None:
    with pytest.raises(HTTPException) as exc:
        drugs.get_drug_pk_observation_math(drug_id, observation_id, 24)
    assert exc.value.status_code == status


@pytest.mark.parametrize("elapsed", [-1, float("inf"), float("nan")])
def test_math_rejects_invalid_time(pk_db: Path, elapsed: float) -> None:
    with pytest.raises(HTTPException) as exc:
        drugs.get_drug_pk_observation_math(
            "vortioxetine", "trintellix-parent-terminal-half-life", elapsed
        )
    assert exc.value.status_code == 422
