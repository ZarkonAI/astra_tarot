from __future__ import annotations

import httpx
from bot.config import Settings
from services.ai.base import BaseAIProvider, AIProviderError


class GeminiProvider(BaseAIProvider):
    name = "gemini"

    def __init__(self, settings: Settings):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model

    async def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIProviderError("GEMINI_API_KEY is missing")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.85, "topP": 0.9, "maxOutputTokens": 1200},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload)
        if response.status_code >= 400:
            raise AIProviderError(f"Gemini API error {response.status_code}: {response.text[:500]}")
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as exc:
            raise AIProviderError(f"Unexpected Gemini response: {data}") from exc
