import json

import pytest

from tools.validate_contributor_claim import _load_json, main


def _valid_submission():
    return {
        "claim_type": "pd_effect",
        "subject": {
            "entity_type": "drug",
            "id": "fluconazole",
        },
        "predicate": "has_pd_effect",
        "object": {
            "effect_id": "QT_prolongation",
        },
        "evidence": [
            {
                "source_id": "source_internal_curated_pd_effects_v1",
                "evidence_type": "internal_curated_entry",
                "supports_claim": True,
                "confidence": "moderate",
                "notes": "Contributor-submitted evidence.",
            }
        ],
        "contributor": {
            "id": "test_contributor",
            "role": "contributor",
            "submitted_at": "2026-05-18",
        },
        "review": {
            "status": "submitted",
        },
    }


def test_load_json_reads_payload(tmp_path):
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps(_valid_submission()),
        encoding="utf-8",
    )

    assert _load_json(path) == _valid_submission()


def test_validate_contributor_claim_tool_prints_success(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps(_valid_submission()),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_contributor_claim",
            str(path),
        ],
    )

    main()

    assert "Contributor claim submission is valid." in capsys.readouterr().out


def test_validate_contributor_claim_tool_prints_draft(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps(_valid_submission()),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_contributor_claim",
            str(path),
            "--draft",
        ],
    )

    main()

    output = json.loads(capsys.readouterr().out)
    assert output["claim_status"] == "draft"
    assert output["claim_id"] == (
        "claim_fluconazole_pd_effect_QT_prolongation_001"
    )


def test_validate_contributor_claim_tool_exits_on_invalid_claim(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps({"claim_type": "pd_effect"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_contributor_claim",
            str(path),
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "Invalid contributor claim submission:" in capsys.readouterr().out