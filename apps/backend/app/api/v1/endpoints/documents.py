from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.document import DocumentResponse, DocumentChunkResponse, DocumentUploadConfig
from app.services.ingestion_service import IngestionService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document into a project workspace"
)
async def upload_document(
    project_id: str = Form(...),
    chunking_strategy: str = Form("recursive"),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    embedding_model: str = Form("text-embedding-3-small"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    config = DocumentUploadConfig(
        chunking_strategy=chunking_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        embedding_model=embedding_model,
    )
    service = IngestionService(db)
    return await service.ingest_file(
        file=file,
        project_id=project_id,
        user=current_user,
        config=config
    )


@router.get(
    "",
    response_model=List[DocumentResponse],
    summary="List all documents in a project workspace"
)
async def list_documents(
    project_id: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = IngestionService(db)
    return await service.list_documents(
        project_id=project_id,
        user=current_user,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document metadata"
)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = IngestionService(db)
    return await service.get_document(document_id, current_user)


@router.get(
    "/{document_id}/chunks",
    response_model=List[DocumentChunkResponse],
    summary="Retrieve all extracted and indexed chunks for a document"
)
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = IngestionService(db)
    return await service.get_document_chunks(document_id, current_user)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document, its chunks, and associated vectors"
)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = IngestionService(db)
    await service.delete_document(document_id, current_user)
    return None
