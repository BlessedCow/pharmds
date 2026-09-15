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


def test_analyze_accepts_pd_effect_filter() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": [
                "vortioxetine",
                "sertraline",
            ],
            "pd_effects": [
                "serotonergic",
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_analyze_rejects_unknown_pd_effect_filter() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drug_names": [
                "vortioxetine",
                "sertraline",
            ],
            "pd_effects": [
                "definitely_not_a_pd_effect",
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "error": "unsupported_pd_effect",
        "unsupported": [
            "definitely_not_a_pd_effect",
        ],
    }

def test_analyze_preserves_selected_dosage_metadata() -> None:
    client = TestClient(app)
    response = client.post(
        "/analyze",
        json={
            "drugs": [
                {
                    "name": "propranolol",
                    "route": "oral",
                    "release_type": "ir",
                    "strength_value": 10,
                    "strength_unit": "mg",
                    "dosage_form": "tablet",
                },
                {
                    "name": "vortioxetine",
                    "route": "oral",
                    "release_type": "ir",
                    "strength_value": 20,
                    "strength_unit": "mg",
                    "dosage_form": "tablet",
                },
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["payload"]["input"]["drug_inputs"] == [
        {
            "drug_id": "propranolol",
            "route": "oral",
            "release_type": "ir",
            "strength_value": 10.0,
            "strength_unit": "mg",
            "dosage_form": "tablet",
        },
        {
            "drug_id": "vortioxetine",
            "route": "oral",
            "release_type": "ir",
            "strength_value": 20.0,
            "strength_unit": "mg",
            "dosage_form": "tablet",
        },
    ]


def test_analyze_preserves_regimen_schedule_context() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze",
        json={
            "drugs": [
                {
                    "name": "propranolol",
                    "route": "oral",
                    "release_type": "ir",
                    "dose_value": 20,
                    "dose_unit": "mg",
                    "frequency": "BID",
                    "schedule_type": "scheduled",
                },
                {
                    "name": "vortioxetine",
                    "route": "oral",
                    "release_type": "ir",
                    "dose_value": 10,
                    "dose_unit": "mg",
                    "frequency": "QD",
                    "schedule_type": "prn",
                    "max_administrations_per_day": 1,
                },
            ],
        },
    )

    assert response.status_code == 200
    drug_inputs = response.json()["payload"]["input"]["drug_inputs"]

    assert drug_inputs[0]["dose_value"] == 20
    assert drug_inputs[0]["frequency"] == "BID"
    assert drug_inputs[0]["frequency_code"] == "bid"
    assert drug_inputs[0]["timing_type"] == "daily_count"
    assert drug_inputs[0]["schedule_type"] == "scheduled"
    assert drug_inputs[0]["inferred_administrations_per_day"] == 2
    assert not drug_inputs[0]["around_the_clock"]

    assert drug_inputs[1]["dose_value"] == 10
    assert drug_inputs[1]["frequency_code"] == "qd"
    assert drug_inputs[1]["timing_type"] == "daily_count"
    assert drug_inputs[1]["schedule_type"] == "prn"
    assert drug_inputs[1]["max_administrations_per_day"] == 1
    assert drug_inputs[1]["inferred_prn_max_administrations_per_day"] == 1
