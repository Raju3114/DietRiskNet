"""Ollama provider unit tests.

All network calls are MOCKED — these tests never require a live Ollama
server.  Live-Ollama verification is covered by the end-to-end smoke
tests (see docs/final/FINAL_OLLAMA_E2E_VALIDATION.md).
"""

from __future__ import annotations

import json
from unittest import mock

import httpx
import pytest

from backend.config import settings
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.services.llm.base import BaseLLMProvider
from backend.services.llm.factory import (
    FallbackLLMProvider,
    LLMProviderFactory,
    get_llm_client,
)
from backend.services.llm.gemini_client import GeminiProvider
from backend.services.llm.ollama_provider import OllamaProvider


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

class _FakeResponse:
    """Mimics ``httpx.Response`` for the provider's success/failure paths."""

    def __init__(self, status_code: int = 200, json_data=None, text: str = "") -> None:
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=self
            )

    def json(self):
        if self._json is None:
            raise ValueError("No JSON body")
        return self._json


class _FakeClient:
    """Mimics ``httpx.Client``; returns pre-scripted responses in order."""

    def __init__(self, *responses: _FakeResponse) -> None:
        self._responses = list(responses)
        self.calls: list = []

    def post(self, url: str, json=None) -> _FakeResponse:
        self.calls.append(("POST", url, json))
        return self._responses.pop(0) if self._responses else _FakeResponse(200, {})

    def get(self, url: str) -> _FakeResponse:
        self.calls.append(("GET", url, None))
        return self._responses.pop(0) if self._responses else _FakeResponse(200, {})

    def __enter__(self) -> "_FakeClient":
        return self

    def __exit__(self, *args) -> bool:
        return False


def _patch_http(*responses: _FakeResponse) -> mock._patch:
    """Patch ``httpx.Client`` with a fake returning *responses* in order."""
    return mock.patch("httpx.Client", return_value=_FakeClient(*responses))


# ----------------------------------------------------------------------
# 1. OllamaProvider initialization / configuration
# ----------------------------------------------------------------------

def test_initialization_uses_settings_defaults():
    p = OllamaProvider()
    assert p.name == "ollama"
    assert p.model == settings.OLLAMA_MODEL
    assert p._url.rstrip("/") == settings.OLLAMA_URL.rstrip("/")


def test_enabled_true_without_gemini_key(monkeypatch):
    # Ollama is a local provider — no API key is required.
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    p = OllamaProvider()
    assert p.enabled is True


# ----------------------------------------------------------------------
# 2. Successful generation
# ----------------------------------------------------------------------

def test_generate_json_success():
    body = json.dumps({"summary": "A balanced meal", "meal_quality": "Good"})
    with _patch_http(_FakeResponse(200, json_data={"response": body})):
        p = OllamaProvider()
        out = p.generate_json("be a dietitian", "context")
    assert out["summary"] == "A balanced meal"
    assert out["meal_quality"] == "Good"


def test_chat_success():
    with _patch_http(_FakeResponse(200, json_data={"response": "Eat oats."})):
        p = OllamaProvider()
        assert p.chat("sys", "suggest breakfast") == "Eat oats."


def test_generate_json_strips_code_fences():
    body = "```json\n{\"reply\": \"hi\"}\n```"
    with _patch_http(_FakeResponse(200, json_data={"response": body})):
        p = OllamaProvider()
        assert p.generate_json("s", "u") == {"reply": "hi"}


# ----------------------------------------------------------------------
# 3. Failure paths
# ----------------------------------------------------------------------

def test_timeout_raises_provider_error():
    def _boom(*args, **kwargs):
        raise httpx.TimeoutException("timed out")

    with mock.patch("httpx.Client") as cls:
        fake = _FakeClient()
        fake.post = _boom
        cls.return_value = fake
        p = OllamaProvider()
        with pytest.raises(LLMProviderError):
            p.generate_json("s", "u")


def test_connection_refused_raises_provider_error():
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    with mock.patch("httpx.Client") as cls:
        fake = _FakeClient()
        fake.post = _boom
        cls.return_value = fake
        p = OllamaProvider()
        with pytest.raises(LLMProviderError):
            p.chat("s", "u")


def test_http_error_raises_provider_error():
    with _patch_http(_FakeResponse(404, text="model not found")):
        p = OllamaProvider()
        with pytest.raises(LLMProviderError):
            p.generate_json("s", "u")


def test_invalid_json_response_raises_provider_error():
    with _patch_http(_FakeResponse(200, json_data={"response": "not json at all"})):
        p = OllamaProvider()
        with pytest.raises(LLMProviderError):
            p.generate_json("s", "u")


def test_empty_response_raises_provider_error():
    with _patch_http(_FakeResponse(200, json_data={"response": "   "})):
        p = OllamaProvider()
        with pytest.raises(LLMProviderError):
            p.generate_json("s", "u")


# ----------------------------------------------------------------------
# 4. Health check
# ----------------------------------------------------------------------

def test_health_check_ok():
    tags = {"models": [{"name": "llama3.2:3b"}, {"name": "mistral"}]}
    with _patch_http(
        _FakeResponse(200, json_data={"version": "0.32.5"}),
        _FakeResponse(200, json_data=tags),
    ):
        p = OllamaProvider()
        hc = p.health_check()
    assert hc["provider"] == "ollama"
    assert hc["status"] == "ok"
    assert hc["version"] == "0.32.5"
    assert hc["detail"] == "model_installed"


def test_health_check_unavailable_does_not_raise():
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("refused")

    with mock.patch("httpx.Client") as cls:
        fake = _FakeClient()
        fake.get = _boom
        cls.return_value = fake
        p = OllamaProvider()
        hc = p.health_check()
    assert hc["status"] == "unavailable"


def test_health_check_reports_model_not_installed():
    tags = {"models": [{"name": "mistral"}]}
    with _patch_http(
        _FakeResponse(200, json_data={"version": "0.32.5"}),
        _FakeResponse(200, json_data=tags),
    ):
        p = OllamaProvider()
        hc = p.health_check()
    assert hc["status"] == "ok"
    assert hc["detail"].startswith("model_not_installed")


# ----------------------------------------------------------------------
# 5. Provider factory / selection
# ----------------------------------------------------------------------

def test_factory_selects_ollama(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    provider = LLMProviderFactory().create_provider()
    assert isinstance(provider, OllamaProvider)


def test_factory_selects_gemini_with_ollama_fallback(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    provider = LLMProviderFactory().create_provider()
    assert isinstance(provider, FallbackLLMProvider)
    assert isinstance(provider._primary, GeminiProvider)
    assert isinstance(provider._fallback, OllamaProvider)


def test_factory_invalid_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "not_a_provider")
    with pytest.raises(ValueError):
        LLMProviderFactory().create_provider()


def test_get_llm_client_returns_provider():
    assert isinstance(get_llm_client(), BaseLLMProvider)


# ----------------------------------------------------------------------
# 6. Gemini -> Ollama fallback behaviour
# ----------------------------------------------------------------------

class _RaisingProvider(BaseLLMProvider):
    name = "raising"
    model = "m"

    @property
    def enabled(self) -> bool:
        return True

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        raise LLMProviderError("primary down")

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        raise LLMProviderError("primary down")

    def health_check(self) -> dict:
        return {
            "provider": self.name,
            "model": self.model,
            "status": "error",
            "latency_ms": 0.0,
            "version": None,
            "detail": "primary down",
        }


class _OkProvider(BaseLLMProvider):
    name = "ok"
    model = "m"

    @property
    def enabled(self) -> bool:
        return True

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {"reply": "fallback-ok"}

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        return "fallback-chat-ok"


def test_fallback_uses_secondary_when_primary_fails():
    fp = FallbackLLMProvider(primary=_RaisingProvider(), fallback=_OkProvider())
    assert fp.generate_json("s", "u") == {"reply": "fallback-ok"}
    assert fp.chat("s", "u") == "fallback-chat-ok"


def test_fallback_raises_when_both_fail():
    fp = FallbackLLMProvider(primary=_RaisingProvider(), fallback=_RaisingProvider())
    with pytest.raises(LLMProviderError):
        fp.generate_json("s", "u")


def test_fallback_health_returns_healthy_secondary():
    fp = FallbackLLMProvider(
        primary=_RaisingProvider(),
        fallback=_OkProvider(),
    )
    hc = fp.health_check()
    assert hc["status"] == "ok"
    assert hc["provider"] == "ok"
