import base64
import requests

from backend.config import get_settings
from backend.models.game import Task
from backend.services.llm.base import (
    MINIGUIDE_SYSTEM_PROMPT,
    TASK_SYSTEM_PROMPT,
    HelpResponse,
    LLMProvider,
    build_guide_user_text,
    build_task_user_text,
    _parse_task,
)

_CLAUDE_API_BASE = "https://api.anthropic.com/v1"
_ANTHROPIC_VERSION = "2023-06-01"


class ClaudeProvider(LLMProvider):
    def generate_guidance(
        self,
        question: str,
        context: str,
        image_png: bytes | None,
        profile_context: str = "",
    ) -> HelpResponse:
        settings = get_settings()
        user_text = build_guide_user_text(question, context, has_image=bool(image_png), profile_context=profile_context)

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
        if not text:
            raise RuntimeError("Claude returned no usable text")
        return HelpResponse(guiding_question=text.strip(), context_used=context)

    def generate_task(self, grade: str, topic: str, difficulty: str, curriculum_context: str = "", profile_context: str = "") -> Task:
        settings = get_settings()
        payload = {
            "model": settings.claude_model,
            "max_tokens": 128,
            "system": TASK_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": build_task_user_text(grade, topic, difficulty, curriculum_context, profile_context)}],
        }
        text = self._call(payload, settings)
        if not text:
            raise RuntimeError("Claude returned no usable text for task generation")
        return _parse_task(text, grade, topic, difficulty)

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
