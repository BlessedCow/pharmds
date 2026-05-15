from tools.backfill_claim_governance import backfill_claim_governance


def test_backfill_claim_governance_adds_default_metadata():
    claims = [
        {
            "claim_id": "claim_fluconazole_pd_effect_QT_prolongation_001",
            "claim_type": "pd_effect",
            "review": {
                "status": "approved",
                "reviewed_by": "maintainer",
                "reviewed_at": None,
            },
        }
    ]

    updated = backfill_claim_governance(claims)

    assert updated[0]["contributor"] == {
        "id": "project_maintainer",
        "role": "maintainer",
        "submitted_at": "2026-05-13",
    }
    assert updated[0]["review"]["reviewed_at"] == "2026-05-13"
    assert "contributor" not in claims[0]