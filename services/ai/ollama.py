from __future__ import annotations

import httpx
from bot.config import Settings
from services.ai.base import BaseAIProvider, AIProviderError


class OllamaProvider(BaseAIProvider):
    name = "ollama"

    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model

    async def generate(self, prompt: str) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.85}}
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
        if response.status_code >= 400:
            raise AIProviderError(f"Ollama API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        return data.get("response", "").strip()
