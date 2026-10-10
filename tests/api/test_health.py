from fastapi.testclient import TestClient

from api.main import app


def test_health_check_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "pharmds-api",
    }


def test_public_api_exposes_only_public_routes() -> None:
    client = TestClient(app)

    paths = client.get("/openapi.json").json()["paths"]
    assert all(
        path.split("/")[1] in {"health", "analyze", "metadata", "drugs"}
        for path in paths
    )
