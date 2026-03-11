import base64
import requests
from fastapi import HTTPException

from backend.config import get_settings
from backend.services.llm.base import LLMProvider


_ANTHROPIC_VERSION = "2023-06-01"


class ClaudeProvider(LLMProvider):
    def call(
        self,
        prompt: str,
        system_prompt: str,
        image_png: bytes | None = None,
    ) -> str:
        settings = get_settings()

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
        content.append({"type": "text", "text": prompt})

        payload = {
            "model": settings.claude_model,
            "max_tokens": 256,
            "system": system_prompt,
            "messages": [{"role": "user", "content": content}],
        }

        text = self._call(payload, settings.claude_api_base, settings.claude_api_key)  # type: ignore
        if not text:
            raise RuntimeError("Claude returned no usable text")
        return text.strip()

    @staticmethod
    def _call(payload: dict, api_base: str, api_key: str) -> str | None:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        response = requests.post(
            f"{api_base}/messages",
            headers=headers,
            json=payload,
            timeout=25,
        )
        if response.status_code == 529:
            raise HTTPException(status_code=503, detail="The AI service is overloaded - please try again in a moment.")
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
