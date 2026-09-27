import re
from typing import List, Dict, Any, Optional
from app.services.chunking.base import BaseChunker, Chunk


class SemanticChunker(BaseChunker):
    """
    Semantic chunking engine.
    Splits text into thematic sentence groupings based on punctuation boundaries
    and accumulates sentences until reaching target semantic capacity.
    """
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        super().__init__(chunk_size, overlap)

    def _split_sentences(self, text: str) -> List[str]:
        # Regex splitting on period, exclamation, question mark followed by space or newline
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = [s.strip() for s in sentence_endings.split(text) if s.strip()]
        return sentences

    def chunk(self, text: str, initial_metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        if not text or not text.strip():
            return []

        sentences = self._split_sentences(text)
        if not sentences:
            return []

        chunks: List[Chunk] = []
        current_sentences: List[str] = []
        current_len = 0
        char_offset = 0
        chunk_idx = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_len + sentence_len > self.chunk_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                meta = dict(initial_metadata or {})
                meta["strategy"] = "semantic"
                meta["sentence_count"] = len(current_sentences)
                chunks.append(
                    Chunk(
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        start_char=char_offset,
                        end_char=char_offset + len(chunk_text),
                        metadata=meta,
                    )
                )
                chunk_idx += 1
                char_offset += len(chunk_text)

                # Overlap: keep the last sentence if possible
                if len(current_sentences) > 1 and len(current_sentences[-1]) <= self.overlap:
                    current_sentences = [current_sentences[-1]]
                    current_len = len(current_sentences[0])
                else:
                    current_sentences = []
                    current_len = 0

            current_sentences.append(sentence)
            current_len += sentence_len + 1

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            meta = dict(initial_metadata or {})
            meta["strategy"] = "semantic"
            meta["sentence_count"] = len(current_sentences)
            chunks.append(
                Chunk(
                    text=chunk_text,
                    chunk_index=chunk_idx,
                    start_char=char_offset,
                    end_char=char_offset + len(chunk_text),
                    metadata=meta,
                )
            )

        return chunks
