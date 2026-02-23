import base64

import requests

from backend.config import get_settings
from backend.services.llm.base import (
    MINIGUIDE_SYSTEM_PROMPT,
    HelpResponse,
    LLMProvider,
    build_guide_user_text,
)

_CLAUDE_API_BASE = "https://api.anthropic.com/v1"
_ANTHROPIC_VERSION = "2023-06-01"


class ClaudeProvider(LLMProvider):
    def guide_student(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
    ) -> HelpResponse:
        settings = get_settings()
        user_text = build_guide_user_text(question, context, has_image=bool(image_png))

        content: list[dict] = []
        if image_png:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64.b64encode(image_png).decode(),
                    },
                }
            )
        content.append({"type": "text", "text": user_text})

        payload = {
            "model": settings.claude_model,
            "max_tokens": 256,
            "system": MINIGUIDE_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": content}],
        }

        text = self._call(payload, settings)
        if text:
            return HelpResponse(
                guiding_question=text.strip(),
                context_used=context,
            )
        raise RuntimeError("Claude returned no usable text")

    @staticmethod
    def _call(payload: dict, settings) -> str | None:
        headers = {
            "x-api-key": settings.claude_api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        response = requests.post(
            f"{_CLAUDE_API_BASE}/messages",
            headers=headers,
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
        return ClaudeProvider._extract_text(response.json())

    @staticmethod
    def _extract_text(result: dict) -> str | None:
        for block in result.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                if text.strip():
                    return text
        return None
