import base64
import time

import requests

from backend.config import get_settings
from backend.services.llm.base import LLMProvider, LLMResult


class GeminiProvider(LLMProvider):
    def call(
        self,
        prompt: str,
        system_prompt: str,
        image_png: bytes | None = None,
    ) -> LLMResult:
        settings = get_settings()

        parts: list[dict] = [{"text": prompt}]
        if image_png:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": base64.b64encode(image_png).decode(),
                    }
                }
            )

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": settings.gemini_temperature, "maxOutputTokens": 256},
        }

        data, latency_ms = self._post(payload, settings.gemini_api_base, settings.gemini_model, settings.gemini_api_key)  # type: ignore
        text = self._extract_text(data)
        if not text:
            raise RuntimeError("Gemini returned no usable text")

        usage = data.get("usageMetadata", {})
        return LLMResult(
            text=text.strip(),
            input_tokens=usage.get("promptTokenCount"),
            output_tokens=usage.get("candidatesTokenCount"),
            latency_ms=latency_ms,
        )

    @staticmethod
    def _post(payload: dict, api_base: str, model: str, api_key: str) -> tuple[dict, float]:
        url = f"{api_base}/models/{model}:generateContent"
        headers = {"X-Goog-Api-Key": api_key}
        start = time.perf_counter()
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        latency_ms = (time.perf_counter() - start) * 1000
        response.raise_for_status()
        return response.json(), latency_ms

    @staticmethod
    def _extract_text(result: dict) -> str | None:
        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text
        return None
