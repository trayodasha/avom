from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    projects,
    documents,
    query,
    datasets,
    evaluations,
    experiments,
    traces,
    dashboard,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(query.router, prefix="/query", tags=["RAG Pipeline"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["Experiments"])
api_router.include_router(traces.router, prefix="/traces", tags=["Traces & Observability"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard & Metrics"])
