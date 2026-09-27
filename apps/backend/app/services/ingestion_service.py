import os
import hashlib
import uuid
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.document import DocumentResponse, DocumentDetailResponse, DocumentChunkResponse, DocumentUploadConfig
from app.repositories.document_repo import DocumentRepository
from app.repositories.project_repo import ProjectRepository
from app.services.parsers.factory import get_parser
from app.services.chunking.factory import get_chunker
from app.services.embeddings.factory import get_embedding_provider
from app.core.vector import get_qdrant_client
from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".docx", ".doc"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.proj_repo = ProjectRepository(db)
        self.qdrant = get_qdrant_client()

    def _get_collection_name(self, project_id: str) -> str:
        # Qdrant collection name formatted with prefix
        clean_id = project_id.replace("-", "_")
        return f"{settings.QDRANT_COLLECTION_PREFIX}{clean_id}"

    def _ensure_qdrant_collection(self, collection_name: str, vector_dim: int) -> None:
        try:
            collections = self.qdrant.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                self.qdrant.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
                )
                logger.info(f"Created Qdrant collection: {collection_name} with dim {vector_dim}")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection {collection_name}: {e}")
            raise

    async def ingest_file(
        self,
        file: UploadFile,
        project_id: str,
        user: User,
        config: DocumentUploadConfig
    ) -> DocumentResponse:
        # 1. Verify project exists and user has access
        project = await self.proj_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        if project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this project workspace."
            )

        # 2. File validation
        filename = file.filename or "uploaded_document"
        ext = os.path.splitext(filename)[-1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        content = await file.read()
        file_size = len(content)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size} bytes) exceeds 50MB limit."
            )

        # 3. Checksum & Deduplication check
        checksum = hashlib.sha256(content).hexdigest()
        existing = await self.doc_repo.get_by_checksum(project_id, checksum)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document '{filename}' with matching checksum already exists in this project."
            )

        # 4. Create initial pending Document record
        doc = Document(
            project_id=project_id,
            filename=filename,
            file_type=ext.replace(".", ""),
            file_size=file_size,
            checksum=checksum,
            status=DocumentStatus.PROCESSING,
            chunk_count=0,
            embedding_model=config.embedding_model,
            chunking_strategy=config.chunking_strategy,
        )
        doc = await self.doc_repo.create(doc)

        try:
            # 5. Parse document
            parser = get_parser(filename)
            parsed = parser.parse(content, filename)

            if not parsed.text.strip():
                raise ValueError("Parsed document yielded empty text content.")

            # 6. Chunking
            chunker = get_chunker(
                strategy=config.chunking_strategy,
                chunk_size=config.chunk_size,
                overlap=config.chunk_overlap
            )
            raw_chunks = chunker.chunk(parsed.text, initial_metadata=parsed.metadata)

            if not raw_chunks:
                raise ValueError("Chunking engine produced 0 chunks from document.")

            # 7. Embeddings
            embed_provider = get_embedding_provider(config.embedding_model)
            texts_to_embed = [c.text for c in raw_chunks]
            embeddings = await embed_provider.embed_documents(texts_to_embed)

            # 8. Qdrant Vector Storage
            collection_name = self._get_collection_name(project_id)
            self._ensure_qdrant_collection(collection_name, embed_provider.dimension)

            points: List[PointStruct] = []
            db_chunks: List[DocumentChunk] = []

            for i, raw_chunk in enumerate(raw_chunks):
                chunk_id = str(uuid.uuid4())
                embedding = embeddings[i]

                # DB Chunk record
                db_chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=doc.id,
                    project_id=project_id,
                    chunk_index=raw_chunk.chunk_index,
                    text_content=raw_chunk.text,
                    start_char=raw_chunk.start_char,
                    end_char=raw_chunk.end_char,
                    metadata_json=raw_chunk.metadata,
                    vector_id=chunk_id,
                )
                db_chunks.append(db_chunk)

                # Qdrant Point
                points.append(
                    PointStruct(
                        id=chunk_id,
                        vector=embedding,
                        payload={
                            "chunk_id": chunk_id,
                            "document_id": doc.id,
                            "project_id": project_id,
                            "filename": filename,
                            "chunk_index": raw_chunk.chunk_index,
                            "text": raw_chunk.text,
                            "metadata": raw_chunk.metadata,
                        }
                    )
                )

            # Batch upsert to Qdrant
            self.qdrant.upsert(
                collection_name=collection_name,
                points=points,
                wait=True
            )

            # 9. Store Chunks in DB and update status
            await self.doc_repo.create_chunks(db_chunks)
            await self.doc_repo.update_status(
                document_id=doc.id,
                status=DocumentStatus.INDEXED,
                chunk_count=len(db_chunks)
            )

            return DocumentResponse.model_validate(doc)

        except Exception as e:
            logger.exception(f"Failed to ingest document '{filename}': {e}")
            await self.doc_repo.update_status(
                document_id=doc.id,
                status=DocumentStatus.FAILED,
                error_message=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document processing failed: {str(e)}"
            )

    async def list_documents(self, project_id: str, user: User, skip: int = 0, limit: int = 100) -> List[DocumentResponse]:
        project = await self.proj_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")

        docs = await self.doc_repo.list_by_project(project_id, skip=skip, limit=limit)
        return [DocumentResponse.model_validate(d) for d in docs]

    async def get_document(self, document_id: str, user: User) -> DocumentResponse:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        project = await self.proj_repo.get_by_id(doc.project_id)
        if project and project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
        return DocumentResponse.model_validate(doc)

    async def get_document_chunks(self, document_id: str, user: User) -> List[DocumentChunkResponse]:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        project = await self.proj_repo.get_by_id(doc.project_id)
        if project and project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")

        chunks = await self.doc_repo.get_chunks_by_document(document_id)
        return [DocumentChunkResponse.model_validate(c) for c in chunks]

    async def delete_document(self, document_id: str, user: User) -> None:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        project = await self.proj_repo.get_by_id(doc.project_id)
        if project and project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")

        # Delete vectors from Qdrant if collection exists
        try:
            chunks = await self.doc_repo.get_chunks_by_document(document_id)
            chunk_ids = [c.id for c in chunks]
            if chunk_ids:
                col_name = self._get_collection_name(doc.project_id)
                self.qdrant.delete(
                    collection_name=col_name,
                    points_selector=chunk_ids
                )
        except Exception as e:
            logger.warning(f"Non-fatal error removing vectors from Qdrant: {e}")

        await self.doc_repo.delete(doc)
