from __future__ import annotations

import httpx
from bot.config import Settings
from services.ai.base import BaseAIProvider, AIProviderError


class GroqProvider(BaseAIProvider):
    name = "groq"

    def __init__(self, settings: Settings):
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIProviderError("GROQ_API_KEY is missing")
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.85, "max_tokens": 1200}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
        if response.status_code >= 400:
            raise AIProviderError(f"Groq API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
