from typing import List, Dict, Any, Optional
from app.services.chunking.base import BaseChunker, Chunk


class FixedSizeChunker(BaseChunker):
    """
    Fixed-size sliding window chunker.
    Steps forward by (chunk_size - overlap) characters.
    """
    def chunk(self, text: str, initial_metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        step = self.chunk_size - self.overlap
        chunks: List[Chunk] = []
        index = 0
        pos = 0

        while pos < len(clean_text):
            end = min(pos + self.chunk_size, len(clean_text))
            chunk_slice = clean_text[pos:end].strip()
            if chunk_slice:
                meta = dict(initial_metadata or {})
                meta["strategy"] = "fixed"
                chunks.append(
                    Chunk(
                        text=chunk_slice,
                        chunk_index=index,
                        start_char=pos,
                        end_char=pos + len(chunk_slice),
                        metadata=meta,
                    )
                )
                index += 1
            if end >= len(clean_text):
                break
            pos += step

        return chunks
