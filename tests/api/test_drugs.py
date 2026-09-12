from fastapi.testclient import TestClient

from api.main import app


def test_drugs_returns_catalog() -> None:
    client = TestClient(app)

    response = client.get("/drugs")

    assert response.status_code == 200

    body = response.json()

    assert "drugs" in body
    assert isinstance(body["drugs"], list)
    assert len(body["drugs"]) > 0


def test_drugs_catalog_contains_release_type_metadata() -> None:
    client = TestClient(app)

    response = client.get("/drugs")

    assert response.status_code == 200

    drugs = {
        drug["id"]: drug
        for drug in response.json()["drugs"]
    }

    assert drugs["venlafaxine"]["release_types"] == [
        "er",
        "ir",
    ]

    assert drugs["vortioxetine"]["release_types"] == [
        "ir",
    ]

    assert drugs["bupropion"]["release_types"] == [
        "er",
        "ir",
        "sr",
    ]

    assert drugs["paliperidone"]["release_types"] == [
        "depot",
        "er",
    ]


def test_drugs_catalog_includes_aliases() -> None:
    client = TestClient(app)

    response = client.get("/drugs")

    assert response.status_code == 200

    drugs = {
        drug["id"]: drug
        for drug in response.json()["drugs"]
    }

    assert "effexor" in drugs["venlafaxine"]["aliases"]
    assert "effexor xr" in drugs["venlafaxine"]["aliases"]
    assert "trintellix" in drugs["vortioxetine"]["aliases"]


def test_drugs_catalog_includes_drug_class() -> None:
    client = TestClient(app)

    response = client.get("/drugs")

    drugs = {
        drug["id"]: drug
        for drug in response.json()["drugs"]
    }

    assert drugs["venlafaxine"]["drug_class"] == "SNRI"
    assert drugs["vortioxetine"]["drug_class"] == (
        "serotonin modulator and stimulator"
    )


def test_get_drug_returns_single_catalog_entry() -> None:
    client = TestClient(app)

    response = client.get("/drugs/venlafaxine")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == "venlafaxine"
    assert body["generic_name"] == "venlafaxine"
    assert body["drug_class"] == "SNRI"
    assert body["aliases"] == [
        "effexor",
        "effexor xr",
    ]
    assert body["release_types"] == [
        "er",
        "ir",
    ]
    assert body["formulations"] == [
        {
            "route": "oral",
            "release_types": [
                "er",
                "ir",
            ],
        }
    ]


def test_get_drug_normalizes_drug_id_case() -> None:
    client = TestClient(app)

    response = client.get("/drugs/VENLAFAXINE")

    assert response.status_code == 200
    assert response.json()["id"] == "venlafaxine"


def test_get_drug_returns_404_for_unknown_drug() -> None:
    client = TestClient(app)

    response = client.get("/drugs/notarealdrug")

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "error": "unknown_drug",
        "drug_id": "notarealdrug",
    }

def test_drugs_catalog_contains_formulation_metadata() -> None:
    client = TestClient(app)

    response = client.get("/drugs")

    assert response.status_code == 200

    drugs = {
        drug["id"]: drug
        for drug in response.json()["drugs"]
    }

    assert drugs["venlafaxine"]["formulations"] == [
        {
            "route": "oral",
            "release_types": [
                "er",
                "ir",
            ],
        }
    ]

    assert drugs["paliperidone"]["formulations"] == [
        {
            "route": "im",
            "release_types": [
                "depot",
            ],
        },
        {
            "route": "oral",
            "release_types": [
                "er",
            ],
        },
    ]