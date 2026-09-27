from typing import List, Dict, Any, Optional
from app.services.chunking.base import BaseChunker, Chunk


class RecursiveCharacterChunker(BaseChunker):
    """
    Hierarchical recursive character chunker.
    Splits text attempting larger semantic boundaries first (paragraphs, sentences, words).
    """
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        separators: Optional[List[str]] = None
    ):
        super().__init__(chunk_size, overlap)
        self.separators = separators or self.DEFAULT_SEPARATORS

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            return list(text)

        sep = separators[0]
        remaining_seps = separators[1:]

        if sep == "":
            return list(text)

        splits = text.split(sep)
        good_splits: List[str] = []

        for i, s in enumerate(splits):
            if not s:
                continue
            # Reattach delimiter to piece (except last piece if no trailing delimiter)
            piece = s + sep if i < len(splits) - 1 else s
            if len(piece) <= self.chunk_size:
                good_splits.append(piece)
            else:
                if remaining_seps:
                    good_splits.extend(self._split_text(piece, remaining_seps))
                else:
                    good_splits.append(piece)

        return good_splits

    def chunk(self, text: str, initial_metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        if not text or not text.strip():
            return []

        raw_splits = self._split_text(text, self.separators)
        chunks: List[Chunk] = []
        current_docs: List[str] = []
        current_len = 0
        char_offset = 0
        chunk_idx = 0

        for split in raw_splits:
            split_len = len(split)
            if current_len + split_len > self.chunk_size and current_docs:
                doc_text = "".join(current_docs).strip()
                if doc_text:
                    meta = dict(initial_metadata or {})
                    meta["strategy"] = "recursive"
                    chunks.append(
                        Chunk(
                            text=doc_text,
                            chunk_index=chunk_idx,
                            start_char=char_offset,
                            end_char=char_offset + len(doc_text),
                            metadata=meta,
                        )
                    )
                    chunk_idx += 1
                    char_offset += len(doc_text)

                # Keep trailing pieces for overlap
                while current_docs and current_len > self.overlap:
                    removed = current_docs.pop(0)
                    current_len -= len(removed)

            current_docs.append(split)
            current_len += split_len

        if current_docs:
            doc_text = "".join(current_docs).strip()
            if doc_text:
                meta = dict(initial_metadata or {})
                meta["strategy"] = "recursive"
                chunks.append(
                    Chunk(
                        text=doc_text,
                        chunk_index=chunk_idx,
                        start_char=char_offset,
                        end_char=char_offset + len(doc_text),
                        metadata=meta,
                    )
                )

        return chunks
