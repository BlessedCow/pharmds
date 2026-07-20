from fastapi.testclient import TestClient

from api.main import app


def test_analyze_requires_at_least_two_drugs() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": ["vortioxetine"],
        },
    )

    assert response.status_code == 422


def test_analyze_returns_400_for_unknown_drug() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": ["vortioxetine", "notarealdrug"],
        },
    )

    assert response.status_code == 400

    body = response.json()

    assert body["detail"]["error"] == "unknown_drug"
    assert body["detail"]["unknown"] == ["notarealdrug"]
    assert body["detail"]["input_drug_names"] == [
        "vortioxetine",
        "notarealdrug",
    ]


def test_analyze_returns_service_payload_for_valid_drugs() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": ["vortioxetine", "propranolol"],
            "domain": "all",
            "qt_risk": False,
            "bleeding_risk": False,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["ok"] is True

    payload = body["payload"]

    assert payload["schema_version"] == "1.0"
    assert payload["input"]["drug_names"] == [
        "vortioxetine",
        "propranolol",
    ]
    assert isinstance(payload["input"]["selected_domains"], list)
    assert "cyp" in payload["input"]["selected_domains"]
    assert "ugt" in payload["input"]["selected_domains"]
    assert "pd" in payload["input"]["selected_domains"]
    assert payload["input"]["patient_flags"] == {
        "qt_risk": False,
        "bleeding_risk": False,
    }
    assert isinstance(payload["pairs"], list)
    assert isinstance(payload["mechanism_pipeline"], dict)
    assert isinstance(payload["public_result_summaries"], list)
