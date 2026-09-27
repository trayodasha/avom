from app.services.chunking.base import BaseChunker, Chunk
from app.services.chunking.fixed import FixedSizeChunker
from app.services.chunking.recursive import RecursiveCharacterChunker
from app.services.chunking.semantic import SemanticChunker


def get_chunker(strategy: str = "recursive", chunk_size: int = 500, overlap: int = 50) -> BaseChunker:
    strat = (strategy or "recursive").lower().strip()
    if strat == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
    elif strat == "semantic":
        return SemanticChunker(chunk_size=chunk_size, overlap=overlap)
    elif strat == "recursive":
        return RecursiveCharacterChunker(chunk_size=chunk_size, overlap=overlap)
    else:
        # Default fallback to recursive
        return RecursiveCharacterChunker(chunk_size=chunk_size, overlap=overlap)
