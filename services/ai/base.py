from __future__ import annotations

from abc import ABC, abstractmethod
from bot.config import Settings
from database.db import Database


class AIProviderError(RuntimeError):
    pass


class BaseAIProvider(ABC):
    name: str
    model: str | None

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError


class AIService:
    def __init__(self, settings: Settings, db: Database):
        self.settings = settings
        self.db = db

    def _provider_order(self) -> list[str]:
        items = [self.settings.ai_provider, self.settings.ai_fallback_1, self.settings.ai_fallback_2, self.settings.ai_fallback_3]
        return [item for item in items if item]

    def _create_provider(self, name: str) -> BaseAIProvider:
        if name == "gemini":
            from services.ai.gemini import GeminiProvider
            return GeminiProvider(self.settings)
        if name == "groq":
            from services.ai.groq import GroqProvider
            return GroqProvider(self.settings)
        if name == "openrouter":
            from services.ai.openrouter import OpenRouterProvider
            return OpenRouterProvider(self.settings)
        if name == "ollama":
            from services.ai.ollama import OllamaProvider
            return OllamaProvider(self.settings)
        raise AIProviderError(f"Unknown AI provider: {name}")

    async def generate(self, prompt: str) -> str:
        errors: list[str] = []
        for provider_name in self._provider_order():
            provider = self._create_provider(provider_name)
            try:
                response = await provider.generate(prompt)
                await self.db.log_ai_usage(provider.name, provider.model, prompt, response, "ok")
                return response
            except Exception as exc:
                error_text = str(exc)
                errors.append(f"{provider_name}: {error_text}")
                await self.db.log_ai_usage(provider.name, provider.model, prompt, None, "error", error_text)
        raise AIProviderError("; ".join(errors))
