import time
from typing import Optional
import httpx
from app.core.config import settings
from app.services.generation.providers.base import BaseLLMProvider, LLMResponse
from app.services.generation.providers.local_provider import LocalDeterministicProvider


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self._model_name = model_name
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._fallback = LocalDeterministicProvider(model_name=model_name)

    @property
    def provider_name(self) -> str:
        return "openai"

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
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(
                url,
                headers=headers,
                json={
                    "model": self._model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            res.raise_for_status()
            data = res.json()
            choice = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            return LLMResponse(
                content=choice,
                model=self._model_name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                latency_ms=elapsed_ms
            )
