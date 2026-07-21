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

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == (
        "Provide at least two drugs (generic or alias)."
    )


def test_analyze_requires_at_least_two_structured_drugs() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drugs": [
                {
                    "name": "vortioxetine",
                    "route": "oral",
                    "release_type": "ir",
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == (
        "Provide at least two drugs (generic or alias)."
    )


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
    assert payload["input"]["pk_timing"] == {
        "route": "oral",
        "release_type": "ir",
        "route_source": "default",
        "release_type_source": "default",
    }
    assert isinstance(payload["pairs"], list)
    assert isinstance(payload["pk_timing_context"], list)
    assert payload["pk_timing_context"][0]["drug_id"] == "vortioxetine"
    assert payload["pk_timing_context"][0]["timing"]["route"] == "oral"
    assert payload["pk_timing_context"][0]["timing"]["release_type"] == "ir"
    assert payload["pk_timing_context"][0]["timing"]["half_life"] == {
        "min_value": 66,
        "max_value": 66,
        "unit": "hours",
    }
    assert payload["pk_timing_context"][1]["drug_id"] == "propranolol"
    assert payload["pk_timing_context"][1]["timing"]["steady_state"] == {
        "min_value": 12,
        "max_value": 30,
        "unit": "hours",
    }
    assert isinstance(payload["pk_timing_interpretation"], list)
    assert payload["pk_timing_interpretation"][0]["drug_id"] == "vortioxetine"
    assert (
        payload["pk_timing_interpretation"][0]["summary"]
        == "Peak timing is about 7-11 hours; half-life is about 66 hours; "
        "steady state is about 14 days."
    )
    assert payload["input"]["pk_timing_by_drug"] == [
        {
            "drug_id": "vortioxetine",
            "route": "oral",
            "release_type": "ir",
            "route_source": "default",
            "release_type_source": "default",
        },
        {
            "drug_id": "propranolol",
            "route": "oral",
            "release_type": "ir",
            "route_source": "default",
            "release_type_source": "default",
        },
    ]
    assert isinstance(payload["mechanism_pipeline"], dict)
    assert isinstance(payload["public_result_summaries"], list)


def test_analyze_accepts_route_and_release_type_for_pk_timing() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": ["propranolol", "vortioxetine"],
            "route": "oral",
            "release_type": "er",
        },
    )

    assert response.status_code == 200

    payload = response.json()["payload"]
    assert payload["input"]["pk_timing"] == {
        "route": "oral",
        "release_type": "er",
        "route_source": "request",
        "release_type_source": "request",
    }
    propranolol_timing = payload["pk_timing_context"][0]["timing"]

    assert propranolol_timing["drug_id"] == "propranolol"
    assert propranolol_timing["route"] == "oral"
    assert propranolol_timing["release_type"] == "er"
    assert propranolol_timing["tmax"] == {
        "min_value": 6,
        "max_value": 10,
        "unit": "hours",
    }
    
    
def test_analyze_prefers_structured_drugs_over_drug_names() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": ["notarealdrug", "alsonotreal"],
            "drugs": [
                {
                    "name": "propranolol",
                    "route": "oral",
                    "release_type": "er",
                },
                {
                    "name": "vortioxetine",
                    "route": "oral",
                    "release_type": "ir",
                },
            ],
        },
    )

    assert response.status_code == 200

    payload = response.json()["payload"]

    assert payload["input"]["drug_names"] == [
        "propranolol",
        "vortioxetine",
    ]
    assert payload["input"]["pk_timing_by_drug"][0]["release_type"] == "er"
    assert payload["input"]["pk_timing_by_drug"][1]["release_type"] == "ir"
    

def test_analyze_accepts_structured_drug_inputs() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drugs": [
                {
                    "name": "propranolol",
                    "route": "oral",
                    "release_type": "er",
                },
                {
                    "name": "vortioxetine",
                    "route": "oral",
                    "release_type": "ir",
                },
            ],
            "route": "oral",
            "release_type": "er",
        },
    )

    assert response.status_code == 200

    payload = response.json()["payload"]

    assert payload["input"]["drug_names"] == [
        "propranolol",
        "vortioxetine",
    ]
    assert payload["input"]["pk_timing"] == {
        "route": "oral",
        "release_type": "er",
        "route_source": "request",
        "release_type_source": "request",
    }
    assert payload["input"]["pk_timing_by_drug"] == [
        {
            "drug_id": "propranolol",
            "route": "oral",
            "release_type": "er",
            "route_source": "drug",
            "release_type_source": "drug",
        },
        {
            "drug_id": "vortioxetine",
            "route": "oral",
            "release_type": "ir",
            "route_source": "drug",
            "release_type_source": "drug",
        },
    ]
    assert payload["pk_timing_context"][0]["timing"]["release_type"] == "er"
    assert payload["pk_timing_context"][1]["timing"]["release_type"] == "ir"
    


def test_analyze_requires_drug_names_or_structured_drugs() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "domain": "all",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Provide either drug_names or drugs."