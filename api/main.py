from __future__ import annotations

from fastapi import FastAPI

from api.routes.analyze import router as analyze_router
from api.routes.health import router as health_router
from api.routes.metadata import router as metadata_router

app = FastAPI(
    title="PharmDS API",
    description="HTTP API for PharmDS medication interaction analysis.",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(metadata_router)