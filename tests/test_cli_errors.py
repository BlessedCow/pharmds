from __future__ import annotations

import pytest

from app.cli import connect, resolve_drug_ids, DB_PATH
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
