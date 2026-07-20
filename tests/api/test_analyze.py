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
    assert "payload" in body
    assert isinstance(body["payload"], dict)
    assert body["payload"]