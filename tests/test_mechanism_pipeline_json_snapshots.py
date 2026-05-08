from app.cli import DB_PATH, connect, load_facts, resolve_drug_ids
from core.mechanism_pipeline import run_mechanism_pipeline
from core.mechanism_pipeline_json import mechanism_pipeline_to_json_dict


def _pipeline_payload_for(names: list[str]):
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, names)
    facts = load_facts(
        conn,
        drug_ids,
        patient_flags={
            "qt_risk": False,
            "bleeding_risk": False,
        },
    )
    pipeline = run_mechanism_pipeline(drug_ids, facts)
    return mechanism_pipeline_to_json_dict(pipeline)


def test_bupropion_vortioxetine_fluconazole_json_snapshot():
    payload = _pipeline_payload_for(
        ["bupropion", "vortioxetine", "fluconazole"],
    )

    aggregate_types = {
        item["aggregate_type"]
        for item in payload["aggregate_concerns"]
    }

    assert "object_exposure_increase_cluster" in aggregate_types
    assert "shared_pd_effect_cluster" in aggregate_types
    assert "tolerability_concern_cluster" in aggregate_types

    exposure_clusters = [
        item
        for item in payload["aggregate_concerns"]
        if item["aggregate_type"] == "object_exposure_increase_cluster"
    ]

    assert len(exposure_clusters) == 1

    exposure_cluster = exposure_clusters[0]

    assert exposure_cluster["anchor"] == "vortioxetine"
    assert exposure_cluster["policy_concern"] == "mechanistic_concern"
    assert exposure_cluster["drugs"] == [
        "bupropion",
        "fluconazole",
        "vortioxetine",
    ]
    assert exposure_cluster["targets"] == [
        "CYP2C19",
        "CYP2C9",
        "CYP2D6",
    ]
    assert len(exposure_cluster["members"]) == 3

    scored_exposure_concerns = [
        item
        for item in payload["scored_concerns"]
        if (
            item["policy_concern"] == "mechanistic_concern"
            and item["object_drug"] == "vortioxetine"
        )
    ]

    assert len(scored_exposure_concerns) == 3

    for concern in scored_exposure_concerns:
        assert concern["confidence"] == "high"
        assert concern["severity"] == "unscored"
        assert concern["aggregate_member_count"] == 3
        assert concern["related_targets"] == [
            "CYP2C19",
            "CYP2C9",
            "CYP2D6",
        ]

    nausea_clusters = [
        item
        for item in payload["aggregate_concerns"]
        if (
            item["aggregate_type"] == "shared_pd_effect_cluster"
            and item["effect_id"] == "nausea"
        )
    ]

    assert len(nausea_clusters) == 1

    nausea_cluster = nausea_clusters[0]

    assert nausea_cluster["anchor"] == "nausea"
    assert nausea_cluster["policy_concern"] == "tolerability_concern"
    assert nausea_cluster["drugs"] == [
        "fluconazole",
        "vortioxetine",
    ]
    assert len(nausea_cluster["members"]) == 1


def test_bupropion_vortioxetine_json_snapshot():
    payload = _pipeline_payload_for(["bupropion", "vortioxetine"])

    exposure_clusters = [
        item
        for item in payload["aggregate_concerns"]
        if item["aggregate_type"] == "object_exposure_increase_cluster"
    ]

    assert len(exposure_clusters) == 1

    exposure_cluster = exposure_clusters[0]

    assert exposure_cluster["anchor"] == "vortioxetine"
    assert exposure_cluster["drugs"] == [
        "bupropion",
        "vortioxetine",
    ]
    assert exposure_cluster["targets"] == ["CYP2D6"]
    assert len(exposure_cluster["members"]) == 1

    scored_concerns = payload["scored_concerns"]

    assert len(scored_concerns) == 1
    assert scored_concerns[0]["policy_concern"] == "mechanistic_concern"
    assert scored_concerns[0]["confidence"] == "high"
    assert scored_concerns[0]["severity"] == "unscored"
    assert scored_concerns[0]["aggregate_member_count"] == 1
    assert scored_concerns[0]["related_targets"] == ["CYP2D6"]