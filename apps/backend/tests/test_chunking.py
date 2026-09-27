import pytest
from app.services.chunking.fixed import FixedSizeChunker
from app.services.chunking.recursive import RecursiveCharacterChunker
from app.services.chunking.semantic import SemanticChunker
from app.services.chunking.factory import get_chunker


def test_fixed_size_chunker():
    chunker = FixedSizeChunker(chunk_size=100, overlap=20)
    sample_text = "A" * 250
    chunks = chunker.chunk(sample_text, initial_metadata={"doc": "test"})
    
    assert len(chunks) > 1
    assert chunks[0].start_char == 0
    assert chunks[0].end_char == 100
    assert chunks[0].metadata["strategy"] == "fixed"
    assert chunks[0].metadata["doc"] == "test"
    # Second chunk should step by (100 - 20) = 80 chars
    assert chunks[1].start_char == 80


def test_recursive_character_chunker_paragraphs():
    text = (
        "Paragraph One is about retrieval engines in modern RAG architectures.\n\n"
        "Paragraph Two discusses reranking with cross-encoders to improve precision.\n\n"
        "Paragraph Three details evaluation metrics including Recall@K and Faithfulness."
    )
    chunker = RecursiveCharacterChunker(chunk_size=120, overlap=20)
    chunks = chunker.chunk(text)
    
    assert len(chunks) >= 3
    assert all(c.metadata["strategy"] == "recursive" for c in chunks)
    assert "Paragraph One" in chunks[0].text
    assert chunks[0].start_char >= 0
    assert chunks[0].end_char > chunks[0].start_char


def test_semantic_chunker_sentences():
    text = (
        "First sentence establishes the premise. "
        "Second sentence extends the proposition further. "
        "Third sentence introduces an alternative view! "
        "Fourth sentence summarizes the core finding."
    )
    chunker = SemanticChunker(chunk_size=100, overlap=30)
    chunks = chunker.chunk(text)
    
    assert len(chunks) >= 2
    assert all(c.metadata["strategy"] == "semantic" for c in chunks)
    assert chunks[0].metadata["sentence_count"] >= 1


def test_chunker_factory():
    c1 = get_chunker("fixed", chunk_size=200, overlap=20)
    assert isinstance(c1, FixedSizeChunker)
    assert c1.chunk_size == 200

    c2 = get_chunker("recursive", chunk_size=300, overlap=30)
    assert isinstance(c2, RecursiveCharacterChunker)
    assert c2.chunk_size == 300

    c3 = get_chunker("semantic", chunk_size=400, overlap=40)
    assert isinstance(c3, SemanticChunker)
    assert c3.chunk_size == 400


def test_empty_text_returns_empty_chunks():
    chunker = RecursiveCharacterChunker(chunk_size=100, overlap=10)
    assert chunker.chunk("") == []
    assert chunker.chunk("   \n\n  ") == []
