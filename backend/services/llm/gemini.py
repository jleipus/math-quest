import base64

import requests

from backend.config import get_settings
from backend.services.llm.base import (
    MINIGUIDE_SYSTEM_PROMPT,
    HelpResponse,
    LLMProvider,
    build_guide_user_text,
)


class GeminiProvider(LLMProvider):
    def guide_student(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
    ) -> HelpResponse:
        settings = get_settings()
        user_text = build_guide_user_text(question, context, has_image=bool(image_png))

        parts: list[dict] = [{"text": user_text}]
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
            "system_instruction": {"parts": [{"text": MINIGUIDE_SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": settings.gemini_temperature,
                "maxOutputTokens": 256,
            },
        }

        text = self._call(payload, settings)
        if text:
            return HelpResponse(
                guiding_question=text.strip(),
                context_used=context,
            )
        raise RuntimeError("Gemini returned no usable text")

    @staticmethod
    def _call(payload: dict, settings) -> str | None:
        url = f"{settings.gemini_api_base}/models/{settings.gemini_model}:generateContent"
        headers = {"X-Goog-Api-Key": settings.gemini_api_key}
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
        if result.get("promptFeedback", {}).get("blockReason"):
            return None
        return None
