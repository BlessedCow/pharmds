from fastapi.testclient import TestClient

from api.main import app


def test_knowledge_status_is_graceful_when_disabled(monkeypatch) -> None:
    monkeypatch.delenv("PHARMDS_RAG_ENABLED", raising=False)
    monkeypatch.delenv("PHARMDS_RAG_BASE_URL", raising=False)
    client = TestClient(app)

    response = client.get("/knowledge/status")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "available": False,
        "base_url_configured": False,
        "detail": "Remote knowledge service is disabled.",
        "model": None,
    }
