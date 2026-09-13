from fastapi.testclient import TestClient

from api.main import app


def test_metadata_returns_frontend_options() -> None:
    client = TestClient(app)

    response = client.get("/metadata")

    assert response.status_code == 200

    body = response.json()

    assert body["domains"] == [
        "all",
        "cyp",
        "ugt",
        "pgp",
        "transporter",
        "pd",
        "pgx",
        "named_pair",
    ]
    assert body["patient_flags"] == [
        "qt_risk",
        "bleeding_risk",
    ]
    assert body["routes"] == [
        "oral",
        "iv",
        "im",
        "sc",
        "transdermal",
        "inhaled",
        "intranasal",
        "sublingual",
        "buccal",
        "rectal",
        "topical",
        "ophthalmic",
        "otic",
        "epidural",
        "intrathecal",
        "vaginal",
        "unknown",
    ]
    assert body["release_types"] == [
        "ir",
        "sr",
        "er",
        "xr",
        "dr",
        "la",
        "depot",
        "unknown",
    ]
    
    pd_effects = body["pd_effects"]

    assert {
        "id": "seizure_risk",
        "label": "Seizure Risk",
    } in pd_effects

    assert {
        "id": "CNS_depression",
        "label": "CNS Depression",
    } in pd_effects

    assert {
        "id": "QT_prolongation",
        "label": "QT Prolongation",
    } in pd_effects

    assert {
        "id": "bleeding",
        "label": "Bleeding Risk",
    } in pd_effects