from app.knowledge_client import knowledge_status, load_knowledge_config


def test_knowledge_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("PHARMDS_RAG_ENABLED", raising=False)
    monkeypatch.delenv("PHARMDS_RAG_BASE_URL", raising=False)
    config = load_knowledge_config()
    assert config.enabled is False
    status = knowledge_status()
    assert status["enabled"] is False
    assert status["available"] is False


def test_enabled_without_base_url_is_graceful(monkeypatch) -> None:
    monkeypatch.setenv("PHARMDS_RAG_ENABLED", "true")
    monkeypatch.delenv("PHARMDS_RAG_BASE_URL", raising=False)
    status = knowledge_status()
    assert status["enabled"] is True
    assert status["available"] is False
    assert status["base_url_configured"] is False
