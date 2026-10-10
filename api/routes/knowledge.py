from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.knowledge_client import knowledge_status, query_knowledge


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSourceResponse(BaseModel):
    title: str | None = None
    citation: str | None = None
    url: str | None = None
    excerpt: str | None = None
    score: float | None = None


class KnowledgeStatusResponse(BaseModel):
    enabled: bool
    available: bool
    base_url_configured: bool
    detail: str | None = None
    model: str | None = None


class KnowledgeQueryResponse(BaseModel):
    informational_only: bool = True
    answer: str
    sources: list[KnowledgeSourceResponse] = Field(default_factory=list)
    model: str | None = None


router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/status", response_model=KnowledgeStatusResponse)
def get_knowledge_status() -> KnowledgeStatusResponse:
    return KnowledgeStatusResponse(**knowledge_status())


@router.post("/query", response_model=KnowledgeQueryResponse)
def query_remote_knowledge(
    request: KnowledgeQueryRequest,
) -> KnowledgeQueryResponse:
    try:
        result = query_knowledge(request.query, top_k=request.top_k)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return KnowledgeQueryResponse(**result)
