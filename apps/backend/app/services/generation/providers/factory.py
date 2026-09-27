from app.services.generation.providers.base import BaseLLMProvider
from app.services.generation.providers.local_provider import LocalDeterministicProvider
from app.services.generation.providers.openai_provider import OpenAIProvider
from app.services.generation.providers.gemini_provider import GeminiProvider


def get_llm_provider(model_name: str = "gpt-4o-mini") -> BaseLLMProvider:
    name = (model_name or "gpt-4o-mini").lower().strip()
    if "gemini" in name:
        return GeminiProvider(model_name=model_name)
    elif "gpt" in name or "openai" in name:
        return OpenAIProvider(model_name=model_name)
    elif "local" in name or "deterministic" in name:
        return LocalDeterministicProvider(model_name=model_name)
    else:
        return OpenAIProvider(model_name=model_name)
