from typing import List
from app.services.retrieval.retriever import RetrievedCandidate

DEFAULT_RAG_SYSTEM_PROMPT = """You are AVOM's precision RAG synthesis assistant.
Your mission is to provide strictly grounded, factual answers to user questions using ONLY the provided retrieved context chunks.

RULES:
1. Ground every claim directly in the context. Do NOT use outside knowledge.
2. If the context does not contain enough information to answer the question, state: "The retrieved context does not contain sufficient information to answer this question."
3. Cite your sources using bracketed numbers like [1], [2] immediately following the statement they support.
4. Keep answers concise, direct, and professional."""


def build_rag_prompt(query: str, context_chunks: List[RetrievedCandidate]) -> str:
    formatted_chunks = []
    for i, chunk in enumerate(context_chunks, start=1):
        formatted_chunks.append(
            f"[{i}] (Document: {chunk.filename})\n{chunk.text.strip()}"
        )

    context_str = "\n\n".join(formatted_chunks) if formatted_chunks else "No relevant context found."

    prompt = f"""--- RETRIEVED CONTEXT ---
{context_str}

--- END CONTEXT ---

User Query: {query}

Instructions: Formulate a grounded response to the User Query citing the relevant [index] numbers."""
    return prompt
