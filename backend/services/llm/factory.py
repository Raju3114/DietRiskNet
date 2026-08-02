"""LLM provider factory.

Selects the concrete provider at runtime from ``settings.LLM_PROVIDER``.

Supported providers:
- ``ollama`` (DEFAULT) — local Ollama server; no API key required.
- ``gemini`` (OPTIONAL) — Google Gemini cloud; requires
  ``GEMINI_API_KEY``.  When selected, requests automatically fall back
  to local Ollama if Gemini fails.

Adding a new provider:
1. implement ``BaseLLMProvider`` in a sibling module,
2. add a branch in ``LLMProviderFactory.create_provider``.

No business-logic changes are required — ``meal_ai_service`` and the
chat services depend only on the ``BaseLLMProvider`` interface.
"""

from __future__ import annotations

from typing import Optional

from backend.config import settings
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.services.llm.base import BaseLLMProvider
from backend.services.llm.gemini_client import GeminiProvider
from backend.services.llm.ollama_provider import OllamaProvider
from backend.utils.logger import app_logger


class FallbackLLMProvider(BaseLLMProvider):
    """Tries the primary provider, then a fallback provider on failure.

    Used so that ``gemini`` (optional cloud) can degrade to local
    ``ollama``.  If both fail, the last error is re-raised so the AI
    services translate it into the existing graceful fallback message —
    never an HTTP 500.
    """

    def __init__(
        self,
        primary: BaseLLMProvider,
        fallback: Optional[BaseLLMProvider] = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback

    @property
    def name(self) -> str:
        return self._primary.name

    @property
    def model(self) -> str:
        return self._primary.model

    @property
    def enabled(self) -> bool:
        if self._primary.enabled:
            return True
        return bool(self._fallback and self._fallback.enabled)

    def _try(self, method_name: str, *args):
        last_error: Optional[LLMProviderError] = None

        if self._primary.enabled:
            try:
                return getattr(self._primary, method_name)(*args)
            except LLMProviderError as exc:
                last_error = exc
                app_logger.warning(
                    "LLM primary '%s' failed (%s); trying fallback '%s'.",
                    self._primary.name,
                    type(exc).__name__,
                    self._fallback.name if self._fallback else "none",
                )

        if self._fallback is not None and self._fallback.enabled:
            return getattr(self._fallback, method_name)(*args)

        if last_error is not None:
            raise last_error
        raise LLMProviderError("No LLM provider is available.")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return self._try("generate_json", system_prompt, user_prompt)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        return self._try("chat", system_prompt, user_prompt)

    def health_check(self) -> dict:
        """Return the first healthy provider's health payload.

        Must never raise.
        """
        for provider in (self._primary, self._fallback):
            if provider is None or not provider.enabled:
                continue
            try:
                result = provider.health_check()
                if result.get("status") == "ok":
                    result["primary"] = self._primary.name
                    if self._fallback is not None:
                        result["fallback"] = self._fallback.name
                    return result
            except Exception:  # noqa: BLE001 — health must never raise
                app_logger.warning(
                    "health probe failed for '%s'; continuing",
                    provider.name,
                )
                continue

        # Nothing reported healthy — report the configured primary state.
        return {
            "provider": self._primary.name,
            "model": self._primary.model,
            "status": "unavailable",
            "latency_ms": 0.0,
            "version": None,
            "detail": "No provider reported healthy.",
            "fallback": self._fallback.name if self._fallback else None,
        }


class LLMProviderFactory:
    """Builds the configured LLM provider (with fallback)."""

    def create_provider(self) -> BaseLLMProvider:
        """Return the provider selected by ``settings.LLM_PROVIDER``.

        Defaults to ``ollama`` when nothing is configured.
        """
        provider = (settings.LLM_PROVIDER or "ollama").strip().lower()

        if provider == "gemini":
            # Gemini is the optional cloud provider.  On failure, requests
            # automatically fall back to a local Ollama instance.
            return FallbackLLMProvider(
                primary=GeminiProvider(),
                fallback=OllamaProvider(),
            )

        if provider == "ollama":
            return OllamaProvider()

        raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")

    def get_provider(self) -> BaseLLMProvider:
        return self.create_provider()


# Backward-compatible helper: services / benchmarks call get_llm_client().
def get_llm_client() -> BaseLLMProvider:
    """Return the configured LLM provider (alias of the factory)."""
    return LLMProviderFactory().get_provider()
