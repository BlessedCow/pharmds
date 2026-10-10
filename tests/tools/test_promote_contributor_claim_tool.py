import json

from tests.evidence.support import contributor_pd_submission
from tools.promote_contributor_claim import _load_json, _write_json, main


def _valid_submission():
    return contributor_pd_submission(
        source_id="source_internal_curated_pd_effects_v1",
        evidence_type="internal_curated_entry",
        evidence_notes="Contributor-submitted evidence.",
        contributor_id="test_contributor",
        contributor_role="contributor",
        submitted_at="2026-05-18",
    )


def test_load_json_reads_payload(tmp_path):
    path = tmp_path / "claim.json"
    path.write_text(
        json.dumps(_valid_submission()),
        encoding="utf-8",
    )

    assert _load_json(path) == _valid_submission()


def test_write_json_writes_pretty_payload(tmp_path):
    path = tmp_path / "approved.json"
    payload = {
        "claim_id": "claim_example_001",
    }

    _write_json(path, payload)

    assert json.loads(path.read_text(encoding="utf-8")) == payload


def test_promote_contributor_claim_tool_prints_approved_claim(
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
            "promote_contributor_claim",
            str(path),
            "--reviewed-by",
            "maintainer",
            "--reviewed-at",
            "2026-05-18",
        ],
    )

    main()

    output = json.loads(capsys.readouterr().out)
    assert output["claim_status"] == "active"
    assert output["review"]["status"] == "approved"


def test_promote_contributor_claim_tool_writes_approved_claim(
    tmp_path,
    monkeypatch,
    capsys,
):
    path = tmp_path / "claim.json"
    out_path = tmp_path / "approved.json"
    path.write_text(
        json.dumps(_valid_submission()),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "promote_contributor_claim",
            str(path),
            "--reviewed-by",
            "maintainer",
            "--reviewed-at",
            "2026-05-18",
            "--out",
            str(out_path),
        ],
    )

    main()

    assert "Wrote approved claim to" in capsys.readouterr().out
    approved = json.loads(out_path.read_text(encoding="utf-8"))
    assert approved["claim_status"] == "active"
    assert approved["review"]["reviewed_by"] == "maintainer"