from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    project_id: str
    chunk_index: int
    text_content: str
    start_char: int
    end_char: int
    metadata_json: Dict[str, Any]
    vector_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_type: str
    file_size: int
    checksum: str
    status: str
    chunk_count: int
    embedding_model: str
    chunking_strategy: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chunks: List[DocumentChunkResponse] = []


class DocumentUploadConfig(BaseModel):
    chunking_strategy: str = Field(default="recursive", description="Strategy: fixed, recursive, semantic")
    chunk_size: int = Field(default=500, ge=50, le=4000, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=50, ge=0, le=1000, description="Overlap between consecutive chunks")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model identifier")
