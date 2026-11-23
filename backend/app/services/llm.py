import logging

import httpx

from ..config import settings

logger = logging.getLogger("zhixueyun.llm")


class LLMGateway:
    @property
    def mode(self) -> str:
        return "online" if settings.llm_enabled else "mock"

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1200,
        json_mode: bool = False,
    ) -> str | None:
        if not settings.llm_enabled:
            return None
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() if isinstance(content, str) and content.strip() else None
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("大模型调用失败，已切换 Mock 兜底: %s", exc)
            return None


llm_gateway = LLMGateway()