from __future__ import annotations

import httpx
from bot.config import Settings
from services.ai.base import BaseAIProvider, AIProviderError


class OpenRouterProvider(BaseAIProvider):
    name = "openrouter"

    def __init__(self, settings: Settings):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIProviderError("OPENROUTER_API_KEY is missing")
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.85, "max_tokens": 1200}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "HTTP-Referer": "https://astra-taro.local", "X-Title": "Astra Taro"},
                json=payload,
            )
        if response.status_code >= 400:
            raise AIProviderError(f"OpenRouter API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
