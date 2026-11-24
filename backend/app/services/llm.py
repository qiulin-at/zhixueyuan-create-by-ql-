import logging

import httpx

from ..config import settings

logger = logging.getLogger("zhixueyun.llm")


class LLMGateway:
    @property
    def mode(self) -> str:
        return "online" if settings.llm_enabled else "mock"

    def _call(
        self,
        base_url: str,
        api_key: str,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str | None:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        url = f"{base_url.rstrip('/')}/chat/completions"
        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip() if isinstance(content, str) and content.strip() else None
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            logger.warning("大模型调用失败（model=%s）: %s", model, exc)
            return None

    def chat_ex(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1200,
        json_mode: bool = False,
        user_config: dict | None = None,
    ) -> tuple[str | None, str]:
        if user_config:
            content = self._call(
                user_config["base_url"],
                user_config["api_key"],
                user_config["model"],
                messages,
                temperature,
                max_tokens,
                json_mode,
            )
            if content:
                return content, "user"
            logger.warning("用户模型调用失败，回退平台模型")
        if settings.llm_enabled:
            content = self._call(
                settings.llm_base_url,
                settings.llm_api_key,
                settings.llm_model,
                messages,
                temperature,
                max_tokens,
                json_mode,
            )
            if content:
                return content, "platform"
        return None, "mock"

    def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1200,
        json_mode: bool = False,
        user_config: dict | None = None,
    ) -> str | None:
        content, _ = self.chat_ex(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
            user_config=user_config,
        )
        return content

    def test_user_config(self, config: dict) -> tuple[bool, str]:
        content = self._call(
            config["base_url"],
            config["api_key"],
            config["model"],
            [{"role": "user", "content": "只回复 OK"}],
            0.0,
            8,
            False,
        )
        if content:
            return True, "连接成功"
        return False, "连接失败，请检查 Key、Base URL 与模型名"


llm_gateway = LLMGateway()