from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import requests

from .config import LLMConfig


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    payload: dict[str, Any]
    raw_text: str


class BaseLLMClient:
    def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise NotImplementedError


def _json_load_with_fallback(raw_text: str) -> dict[str, Any]:
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw_text[start : end + 1])
            except json.JSONDecodeError as exc:
                raise LLMError(f"Model returned invalid JSON: {exc}") from exc
        raise LLMError("Model returned non-JSON content")


def _normalize_openai_url(base_url: str | None) -> str:
    if not base_url:
        return "https://api.openai.com/v1/chat/completions"
    if base_url.endswith("/v1/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url.rstrip('/')}/v1/chat/completions"


def _normalize_openrouter_url(base_url: str | None) -> str:
    if not base_url:
        return "https://openrouter.ai/api/v1/chat/completions"
    if base_url.endswith("/chat/completions"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/chat/completions"
    return f"{base_url.rstrip('/')}/chat/completions"


def _normalize_ollama_url(base_url: str | None) -> str:
    if not base_url:
        return "http://localhost:11434/api/chat"
    if base_url.endswith("/api/chat"):
        return base_url
    return f"{base_url.rstrip('/')}/api/chat"


def _load_api_key(config: LLMConfig, fallback_env: str | None = None) -> tuple[str, str]:
    key = os.getenv(config.api_key_env)
    env_name = config.api_key_env
    if not key and fallback_env:
        key = os.getenv(fallback_env)
        if key:
            env_name = fallback_env
    if not key:
        expected = f"{config.api_key_env}" if not fallback_env else f"{config.api_key_env} or {fallback_env}"
        raise LLMError(f"Missing API key in env var {expected}. Set it before running the harness.")
    return key, env_name


class MockClient(BaseLLMClient):
    def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        payload = {
            "spec_path": "specs/AutoSpec.cvl",
            "certora_command": "echo MOCK_CERTORA_OK && true",
            "summary": "Mock response for dry-run and plumbing checks.",
            "spec": "invariant mock_invariant_true() true;\n",
        }
        return LLMResponse(payload=payload, raw_text=json.dumps(payload))


class OpenAIClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key, _ = _load_api_key(config)
        self.url = _normalize_openai_url(config.base_url)

    def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.config.max_output_tokens,
        }
        response = requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout_sec,
        )
        if response.status_code >= 400:
            raise LLMError(f"OpenAI request failed: {response.status_code} {response.text}")

        data = response.json()
        try:
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected OpenAI response shape: {data}") from exc

        parsed = _json_load_with_fallback(raw_text)
        return LLMResponse(payload=parsed, raw_text=raw_text)


class OpenRouterClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key, self.key_env_name = _load_api_key(config, fallback_env="OPENROUTER_API_KEY")
        self.url = _normalize_openrouter_url(config.base_url)

    def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        title = os.getenv("OPENROUTER_X_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title

        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": self.config.max_output_tokens,
        }
        response = requests.post(
            self.url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout_sec,
        )
        if response.status_code >= 400:
            raise LLMError(f"OpenRouter request failed: {response.status_code} {response.text}")

        data = response.json()
        try:
            raw_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected OpenRouter response shape: {data}") from exc

        parsed = _json_load_with_fallback(raw_text)
        return LLMResponse(payload=parsed, raw_text=raw_text)


class OllamaClient(BaseLLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.url = _normalize_ollama_url(config.base_url)

    def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        payload = {
            "model": self.config.model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": self.config.temperature,
            },
        }
        response = requests.post(self.url, json=payload, timeout=self.config.timeout_sec)
        if response.status_code >= 400:
            raise LLMError(f"Ollama request failed: {response.status_code} {response.text}")

        data = response.json()
        try:
            raw_text = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Unexpected Ollama response shape: {data}") from exc

        parsed = _json_load_with_fallback(raw_text)
        return LLMResponse(payload=parsed, raw_text=raw_text)


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    provider = config.provider.strip().lower()
    if provider == "openai":
        return OpenAIClient(config)
    if provider == "openrouter":
        return OpenRouterClient(config)
    if provider == "ollama":
        return OllamaClient(config)
    if provider == "mock":
        return MockClient()
    raise LLMError(f"Unsupported provider: {config.provider}")
