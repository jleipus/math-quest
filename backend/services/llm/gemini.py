import base64
import requests

from backend.config import get_settings
from backend.services.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    def call(
        self,
        prompt: str,
        system_prompt: str,
        image_png: bytes | None = None,
    ) -> str:
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

        text = self._call(payload, settings.gemini_api_base, settings.gemini_model, settings.gemini_api_key)  # type: ignore
        if not text:
            raise RuntimeError("Gemini returned no usable text")
        return text.strip()

    @staticmethod
    def _call(payload: dict, api_base: str, model: str, api_key: str) -> str | None:
        url = f"{api_base}/models/{model}:generateContent"
        headers = {"X-Goog-Api-Key": api_key}
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
        return GeminiProvider._extract_text(response.json())

    @staticmethod
    def _extract_text(result: dict) -> str | None:
        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text
        return None
