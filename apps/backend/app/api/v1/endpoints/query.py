from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_pipeline import RAGPipeline
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute end-to-end RAG query with hybrid retrieval, cross-encoder reranking, and citation tracing"
)
async def query_pipeline(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pipeline = RAGPipeline(db)
    return await pipeline.execute_query(request, current_user)
