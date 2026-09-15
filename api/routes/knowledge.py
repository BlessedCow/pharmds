from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from api.models import (
    KnowledgeQueryRequest,
    KnowledgeQueryResponse,
    KnowledgeStatusResponse,
)
from app.knowledge_client import knowledge_status, query_knowledge

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
