"""OpenRouter client providing centralized remote LLM access."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Union
from urllib import error, request


class OpenRouterError(RuntimeError):
    """Raised when an OpenRouter request cannot be completed."""


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class CompletionUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class CompletionResult:
    model: str
    message: ChatMessage
    finish_reason: Optional[str]
    usage: CompletionUsage
    raw: Dict[str, Any]


class OpenRouterClient:
    """Thin HTTP client around the OpenRouter chat completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: float = 60.0,
        app_url: Optional[str] = None,
        app_name: Optional[str] = None,
    ) -> None:
        key = (api_key or os.getenv("OPENROUTER_API_KEY", "")).strip()
        if not key:
            raise OpenRouterError("Missing OpenRouter credentials (set OPENROUTER_API_KEY)")
        self.base_url = (base_url or os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1").rstrip("/")
        self.timeout_s = timeout_s
        self._headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        referer = (app_url or os.getenv("OPENROUTER_APP_URL", "")).strip()
        if referer:
            self._headers["HTTP-Referer"] = referer
        title = (app_name or os.getenv("OPENROUTER_APP_NAME", "")).strip()
        if title:
            self._headers["X-Title"] = title

    def chat_completion(
        self,
        *,
        model: str,
        messages: Sequence[Union[ChatMessage, Mapping[str, Any]]],
        temperature: float = 0.0,
        max_output_tokens: Optional[int] = None,
        response_format: Optional[Mapping[str, Any]] = None,
        metadata: Optional[Mapping[str, Any]] = None,
        **extra_settings: Any,
    ) -> CompletionResult:
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [self._serialize_message(message) for message in messages],
            "temperature": temperature,
        }
        if max_output_tokens is not None:
            payload["max_tokens"] = max_output_tokens
        if response_format:
            payload["response_format"] = response_format
        if metadata:
            payload["metadata"] = dict(metadata)
        if extra_settings:
            payload.update(extra_settings)

        response = self._post("/chat/completions", payload)
        choice = self._first_choice(response)
        message_payload = choice.get("message") or {}
        content = self._extract_content(message_payload.get("content"))
        message = ChatMessage(role=message_payload.get("role", "assistant"), content=content)
        usage_payload = response.get("usage") or {}
        usage = CompletionUsage(
            input_tokens=int(
                usage_payload.get("prompt_tokens")
                or usage_payload.get("input_tokens")
                or 0
            ),
            output_tokens=int(
                usage_payload.get("completion_tokens")
                or usage_payload.get("output_tokens")
                or 0
            ),
            total_tokens=int(usage_payload.get("total_tokens") or 0),
        )
        if usage.total_tokens == 0:
            usage.total_tokens = usage.input_tokens + usage.output_tokens
        return CompletionResult(
            model=response.get("model", model),
            message=message,
            finish_reason=choice.get("finish_reason"),
            usage=usage,
            raw=response,
        )

    def _serialize_message(self, message: Union[ChatMessage, Mapping[str, Any]]) -> Dict[str, Any]:
        if isinstance(message, ChatMessage):
            return {"role": message.role, "content": message.content}
        role = str(message.get("role", "user"))
        content = message.get("content", "")
        if isinstance(content, list):
            return {"role": role, "content": content}
        return {"role": role, "content": str(content)}

    def _post(self, path: str, payload: Mapping[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, method="POST", headers=self._headers)
        try:
            with request.urlopen(req, timeout=self.timeout_s) as response:
                body = response.read()
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise OpenRouterError(f"OpenRouter request failed: {exc.code} {detail}") from exc
        except error.URLError as exc:  # pragma: no cover - network errors only at runtime
            raise OpenRouterError(f"Unable to reach OpenRouter: {exc.reason}") from exc

        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - unexpected API change
            raise OpenRouterError("Invalid JSON payload returned by OpenRouter") from exc

    @staticmethod
    def _first_choice(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        choices = payload.get("choices")
        if not choices:
            raise OpenRouterError("OpenRouter response did not include choices")
        return choices[0]

    @staticmethod
    def _extract_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            fragments = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    fragments.append(str(item["text"]))
            return "\n".join(fragments)
        return "" if content is None else str(content)
