from app.cli import DB_PATH, connect, load_facts, resolve_drug_ids
from core.mechanisms import (
    mechanism_pipeline_to_json_dict,
    run_mechanism_pipeline,
)


def _pipeline_payload_for(
    names: list[str],
    patient_flags: dict[str, bool] | None = None,
):
    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, names)
    facts = load_facts(
        conn,
        drug_ids,
        patient_flags=patient_flags
        or {
            "qt_risk": False,
            "bleeding_risk": False,
        },
    )
    pipeline = run_mechanism_pipeline(drug_ids, facts)
    return mechanism_pipeline_to_json_dict(pipeline)

def _aggregate_summary_by(
    payload: dict,
    aggregate_type: str,
    anchor: str,
) -> dict:
    return next(
        summary
        for summary in payload["aggregate_concern_summaries"]
        if (
            summary["aggregate"]["aggregate_type"] == aggregate_type
            and summary["aggregate"]["anchor"] == anchor
        )
    )


def _assert_aggregate_summary_json_shape(summary: dict):
    assert set(summary) == {
        "aggregate",
        "severity_annotation",
        "evidence_summary",
        "patient_risk_modifiers",
        "risk_context",
        "evidence_conflict_level",
        "evidence_conflict_message",
        "evidence_conflict_source_ids",
        "evidence_conflict_trace_types",
        "evidence_conflict_reasons",
        "narrative",
    }

    assert isinstance(summary["aggregate"], dict)
    assert (
        isinstance(summary["severity_annotation"], dict)
        or summary["severity_annotation"] is None
    )
    assert (
        isinstance(summary["evidence_summary"], dict)
        or summary["evidence_summary"] is None
    )
    assert isinstance(summary["patient_risk_modifiers"], list)
    assert (
        isinstance(summary["risk_context"], str)
        or summary["risk_context"] is None
    )
    assert isinstance(summary["evidence_conflict_level"], str)
    assert (
        isinstance(summary["evidence_conflict_message"], str)
        or summary["evidence_conflict_message"] is None
    )
    assert isinstance(summary["evidence_conflict_source_ids"], list)
    assert isinstance(summary["evidence_conflict_trace_types"], list)
    assert isinstance(summary["evidence_conflict_reasons"], list)
    assert isinstance(summary["narrative"], str)
    
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
    severity_annotations = [
        item
        for item in payload["severity_annotations"]
        if (
            item["scored"]["policy_concern"] == "mechanistic_concern"
            and item["scored"]["object_drug"] == "vortioxetine"
        )
    ]

    assert len(severity_annotations) == 3

    for annotation in severity_annotations:
        assert annotation["preliminary_severity"] == "caution"
        assert annotation["severity_reason"] == (
            "Multiple mechanism candidates affect the same object drug."
        )
        assert annotation["scored"]["confidence"] == "high"
        assert annotation["scored"]["aggregate_member_count"] == 3
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
    severity_annotations = [
        item
        for item in payload["severity_annotations"]
        if (
            item["scored"]["policy_concern"] == "mechanistic_concern"
            and item["scored"]["object_drug"] == "vortioxetine"
        )
    ]

    assert len(severity_annotations) == 3

    for annotation in severity_annotations:
        assert annotation["preliminary_severity"] == "caution"
        assert annotation["severity_reason"] == (
            "Multiple mechanism candidates affect the same object drug."
        )
        assert annotation["scored"]["confidence"] == "high"
        assert annotation["scored"]["aggregate_member_count"] == 3
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

    severity_annotations = payload["severity_annotations"]

    assert len(severity_annotations) == 1
    assert severity_annotations[0]["preliminary_severity"] == "informational"
    assert severity_annotations[0]["severity_reason"] == (
        "Single high-confidence mechanistic concern."
    )
    assert severity_annotations[0]["scored"]["confidence"] == "high"

def test_clarithromycin_fluconazole_aggregate_summary_json_snapshot():
    payload = _pipeline_payload_for(["clarithromycin", "fluconazole"])

    assert len(payload["aggregate_concern_summaries"]) == 4

    for summary in payload["aggregate_concern_summaries"]:
        _assert_aggregate_summary_json_shape(summary)

    qt_summary = _aggregate_summary_by(
        payload,
        "shared_pd_effect_cluster",
        "QT_prolongation",
    )

    assert qt_summary["aggregate"]["policy_concern"] == "safety_concern"
    assert qt_summary["aggregate"]["drugs"] == [
        "clarithromycin",
        "fluconazole",
    ]
    assert qt_summary["aggregate"]["effect_id"] == "QT_prolongation"
    assert (
        qt_summary["severity_annotation"]["strongest_preliminary_severity"]
        == "high_caution"
    )
    assert (
        qt_summary["evidence_summary"]["overall_evidence_status"]
        == "complete"
    )
    assert qt_summary["patient_risk_modifiers"] == []
    assert qt_summary["risk_context"] is None
    assert qt_summary["evidence_conflict_level"] == "none"
    assert qt_summary["evidence_conflict_message"] is None
    assert qt_summary["evidence_conflict_source_ids"] == []
    assert qt_summary["evidence_conflict_trace_types"] == []
    assert (
        "QT prolongation-related pharmacodynamic concerns"
        in qt_summary["narrative"]
    )
    assert (
        "Curated evidence support for this grouped concern is complete"
        in qt_summary["narrative"]
    )
    assert (
        "Preliminary educational severity: High caution"
        in qt_summary["narrative"]
    )
    assert "educational and not diagnostic" in qt_summary["narrative"]

    nausea_summary = _aggregate_summary_by(
        payload,
        "shared_pd_effect_cluster",
        "nausea",
    )

    assert nausea_summary["aggregate"]["policy_concern"] == (
        "tolerability_concern"
    )
    assert nausea_summary["aggregate"]["drugs"] == [
        "clarithromycin",
        "fluconazole",
    ]
    assert nausea_summary["aggregate"]["effect_id"] == "nausea"
    assert (
        nausea_summary["severity_annotation"]["strongest_preliminary_severity"]
        == "informational"
    )
    assert (
        nausea_summary["evidence_summary"]["overall_evidence_status"]
        == "complete"
    )
    assert nausea_summary["evidence_conflict_level"] == "none"
    assert (
        "nausea-related pharmacodynamic concern"
        in nausea_summary["narrative"]
    )


def test_bupropion_vortioxetine_aggregate_summary_json_snapshot():
    payload = _pipeline_payload_for(["bupropion", "vortioxetine"])

    assert len(payload["aggregate_concern_summaries"]) == 1

    summary = _aggregate_summary_by(
        payload,
        "object_exposure_increase_cluster",
        "vortioxetine",
    )

    _assert_aggregate_summary_json_shape(summary)

    assert summary["aggregate"]["policy_concern"] == "mechanistic_concern"
    assert summary["aggregate"]["drugs"] == [
        "bupropion",
        "vortioxetine",
    ]
    assert summary["aggregate"]["targets"] == ["CYP2D6"]
    assert summary["aggregate"]["effect_id"] is None
    assert len(summary["aggregate"]["members"]) == 1

    assert (
        summary["severity_annotation"]["strongest_preliminary_severity"]
        == "informational"
    )
    assert (
        summary["evidence_summary"]["overall_evidence_status"]
        == "not_applicable"
    )
    assert summary["evidence_summary"]["evidence_claim_count"] == 0
    assert summary["evidence_summary"]["evidence_gap_count"] == 0

    assert summary["patient_risk_modifiers"] == []
    assert summary["risk_context"] is None
    assert summary["evidence_conflict_level"] == "none"
    assert summary["evidence_conflict_message"] is None
    assert summary["evidence_conflict_source_ids"] == []
    assert summary["evidence_conflict_trace_types"] == []

    assert (
        "This regimen includes bupropion and vortioxetine, with mechanism(s) that may "
        "increase vortioxetine exposure through CYP2D6-related mechanism(s)."
    ) in summary["narrative"]
    assert "not required at the aggregate level" in summary["narrative"]
    assert (
        "Preliminary educational severity: Informational"
        in summary["narrative"]
    )
    assert "educational and not diagnostic" in summary["narrative"]


def test_alcohol_clonazepam_aggregate_summary_json_snapshot():
    payload = _pipeline_payload_for(["alcohol", "clonazepam"])

    assert len(payload["aggregate_concern_summaries"]) == 5

    for summary in payload["aggregate_concern_summaries"]:
        _assert_aggregate_summary_json_shape(summary)

    respiratory_summary = _aggregate_summary_by(
        payload,
        "shared_pd_effect_cluster",
        "respiratory_depression",
    )

    assert respiratory_summary["aggregate"]["policy_concern"] == (
        "safety_concern"
    )
    assert respiratory_summary["aggregate"]["drugs"] == [
        "alcohol",
        "clonazepam",
    ]
    assert respiratory_summary["aggregate"]["effect_id"] == (
        "respiratory_depression"
    )
    assert (
        respiratory_summary["severity_annotation"][
            "strongest_preliminary_severity"
        ]
        == "high_caution"
    )
    assert (
        respiratory_summary["evidence_summary"]["overall_evidence_status"]
        == "complete"
    )
    assert respiratory_summary["evidence_conflict_level"] == "none"
    assert (
        "respiratory depression-related pharmacodynamic concern"
        in respiratory_summary["narrative"]
    )

    cns_summary = _aggregate_summary_by(
        payload,
        "shared_pd_effect_cluster",
        "CNS_depression",
    )

    assert cns_summary["aggregate"]["policy_concern"] == (
        "tolerability_concern"
    )
    assert cns_summary["aggregate"]["effect_id"] == "CNS_depression"
    assert (
        cns_summary["severity_annotation"]["strongest_preliminary_severity"]
        == "caution"
    )
    assert cns_summary["evidence_conflict_level"] == "none"
    assert (
        "CNS depression-related pharmacodynamic concern"
        in cns_summary["narrative"]
    )

    sedation_summary = _aggregate_summary_by(
        payload,
        "shared_pd_effect_cluster",
        "sedation",
    )

    assert sedation_summary["aggregate"]["policy_concern"] == (
        "tolerability_concern"
    )
    assert sedation_summary["aggregate"]["effect_id"] == "sedation"
    assert (
        sedation_summary["severity_annotation"][
            "strongest_preliminary_severity"
        ]
        == "caution"
    )
    assert sedation_summary["evidence_conflict_level"] == "none"
    assert (
        "sedation-related pharmacodynamic concern"
        in sedation_summary["narrative"]
    )


def test_qt_risk_aggregate_summary_json_snapshot():
    payload = _pipeline_payload_for(
        ["clarithromycin", "fluconazole"],
        patient_flags={
            "qt_risk": True,
            "bleeding_risk": False,
        },
    )

    qt_summary = _aggregate_summary_by(
        payload,
        "shared_pd_effect_cluster",
        "QT_prolongation",
    )

    _assert_aggregate_summary_json_shape(qt_summary)

    assert qt_summary["patient_risk_modifiers"] == ["qt_risk"]
    assert qt_summary["risk_context"] == (
        "QT-related concerns may be more relevant when a QT risk flag is present."
    )
    assert "Patient risk flag present: QT risk." in qt_summary["narrative"]
    assert "QT-related concerns may be more relevant" in qt_summary["narrative"]