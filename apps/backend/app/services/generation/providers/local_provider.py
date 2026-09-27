import time
import re
from typing import List
from app.services.generation.providers.base import BaseLLMProvider, LLMResponse


class LocalDeterministicProvider(BaseLLMProvider):
    """
    Offline/local fallback provider that performs deterministic, grounded synthesis
    directly from the assembled prompt context, inserting proper citation markers.
    Used for local testing, CI environments, and when external API keys are unset.
    """
    def __init__(self, model_name: str = "local-deterministic"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "local"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        start_time = time.time()

        # Extract context blocks like [1] ... [2] ...
        context_blocks = re.findall(r'\[(\d+)\]\s+(.*?)(?=\[\d+\]|$)', prompt, re.DOTALL)
        
        # Extract user query
        query_match = re.search(r'User Query:\s*(.*?)(?=\n|$)', prompt, re.IGNORECASE)
        query = query_match.group(1).strip() if query_match else "the query"

        if not context_blocks:
            content = f"Based on the provided context, I cannot find relevant information to answer: '{query}'."
        else:
            # Construct a grounded answer citing the highest ranked chunks
            statements = []
            for num, block_text in context_blocks[:3]:
                # Extract first meaningful sentence from the chunk
                cleaned = " ".join(block_text.strip().splitlines())
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if len(s.strip()) > 10]
                if sentences:
                    statements.append(f"{sentences[0]} [{num}]")

            if statements:
                content = " ".join(statements)
            else:
                content = f"The retrieved documents address '{query}' as documented in the provided knowledge base [{context_blocks[0][0]}]."

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        in_tokens = len(prompt.split())
        out_tokens = len(content.split())

        return LLMResponse(
            content=content,
            model=self._model_name,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_ms=elapsed_ms
        )
