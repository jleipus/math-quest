import base64
import time

import requests
from fastapi import HTTPException

from backend.config import get_settings
from backend.services.llm.base import LLMProvider, LLMResult


_ANTHROPIC_VERSION = "2023-06-01"


class ClaudeProvider(LLMProvider):
    def call(
        self,
        prompt: str,
        system_prompt: str,
        image_png: bytes | None = None,
    ) -> LLMResult:
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

        data, latency_ms = self._post(payload, settings.claude_api_base, settings.claude_api_key)  # type: ignore
        text = self._extract_text(data)
        if not text:
            raise RuntimeError("Claude returned no usable text")

        usage = data.get("usage", {})
        return LLMResult(
            text=text.strip(),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            latency_ms=latency_ms,
        )

    @staticmethod
    def _post(payload: dict, api_base: str, api_key: str) -> tuple[dict, float]:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }
        start = time.perf_counter()
        response = requests.post(
            f"{api_base}/messages",
            headers=headers,
            json=payload,
            timeout=25,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code == 529:
            raise HTTPException(status_code=503, detail="The AI service is overloaded - please try again in a moment.")
        response.raise_for_status()
        return response.json(), latency_ms

    @staticmethod
    def _extract_text(result: dict) -> str | None:
        for block in result.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                if text.strip():
                    return text
        return None
