import time
from typing import Optional
import httpx
from app.core.config import settings
from app.services.generation.providers.base import BaseLLMProvider, LLMResponse
from app.services.generation.providers.local_provider import LocalDeterministicProvider


class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self._model_name = model_name
        self.api_key = api_key or settings.GEMINI_API_KEY
        self._fallback = LocalDeterministicProvider(model_name=model_name)

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        if not self.api_key:
            return await self._fallback.generate(prompt, system_prompt, temperature, max_tokens)

        start_time = time.time()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            candidate = data["candidates"][0]["content"]["parts"][0]["text"]
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return LLMResponse(
                content=candidate,
                model=self._model_name,
                input_tokens=len(full_prompt.split()),
                output_tokens=len(candidate.split()),
                latency_ms=elapsed_ms
            )
