from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class KnowledgeConfig:
    enabled: bool
    base_url: str | None
    api_key: str | None
    timeout_seconds: float


def load_knowledge_config() -> KnowledgeConfig:
    enabled = os.getenv("PHARMDS_RAG_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on"
    }
    base_url = os.getenv("PHARMDS_RAG_BASE_URL", "").strip().rstrip("/") or None
    api_key = os.getenv("PHARMDS_RAG_API_KEY", "").strip() or None
    timeout = float(os.getenv("PHARMDS_RAG_TIMEOUT_SECONDS", "5"))
    return KnowledgeConfig(enabled, base_url, api_key, timeout)


def _request_json(
    config: KnowledgeConfig,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not config.enabled:
        raise RuntimeError("Remote knowledge service is disabled.")
    if config.base_url is None:
        raise RuntimeError("PHARMDS_RAG_BASE_URL is not configured.")

    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    request = Request(
        f"{config.base_url}{path}",
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )
    try:
        with urlopen(request, timeout=config.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(
            f"Remote knowledge service returned HTTP {exc.code}."
        ) from exc
    except URLError as exc:
        raise RuntimeError("Remote knowledge service is unavailable.") from exc


def knowledge_status() -> dict[str, Any]:
    config = load_knowledge_config()
    if not config.enabled:
        return {
            "enabled": False,
            "available": False,
            "base_url_configured": config.base_url is not None,
            "detail": "Remote knowledge service is disabled.",
            "model": None,
        }
    if config.base_url is None:
        return {
            "enabled": True,
            "available": False,
            "base_url_configured": False,
            "detail": "PHARMDS_RAG_BASE_URL is not configured.",
            "model": None,
        }
    try:
        remote = _request_json(config, "/health")
    except RuntimeError as exc:
        return {
            "enabled": True,
            "available": False,
            "base_url_configured": True,
            "detail": str(exc),
            "model": None,
        }
    return {
        "enabled": True,
        "available": True,
        "base_url_configured": True,
        "detail": remote.get("detail"),
        "model": remote.get("model"),
    }


def query_knowledge(query: str, *, top_k: int = 5) -> dict[str, Any]:
    config = load_knowledge_config()
    remote = _request_json(
        config,
        "/query",
        payload={"query": query, "top_k": top_k},
    )
    return {
        "informational_only": True,
        "answer": str(remote.get("answer") or ""),
        "sources": list(remote.get("sources") or []),
        "model": remote.get("model"),
    }
