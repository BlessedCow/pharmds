from __future__ import annotations

import pytest

from app.cli import connect, resolve_drug_ids, DB_PATH
from core.exceptions import UnknownDrugError


def test_unknown_drug_has_suggestions_for_close_match():
    conn = connect(DB_PATH)

    # Intentionally misspell a seeded drug. "quetiapine" is in your seed set.
    with pytest.raises(UnknownDrugError) as exc:
        resolve_drug_ids(conn, ["quetiaipne"])

    err = exc.value
    assert "quetiaipne" in err.unknown
    # Ensure we got at least one suggestion and that quetiapine is among them
    assert "quetiapine" in err.suggestions.get("quetiaipne", ())


def test_unknown_drug_may_have_no_suggestions_for_gibberish():
    conn = connect(DB_PATH)

    with pytest.raises(UnknownDrugError) as exc:
        resolve_drug_ids(conn, ["xqznotadrug"])

    err = exc.value
    assert "xqznotadrug" in err.unknown
    assert err.suggestions.get("xqznotadrug", ()) == ()
