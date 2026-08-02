"""Provider-agnostic LLM interface.

Every AI feature (AI Dietitian, meal-specific chat, AI Nutrition
Assistant) depends only on this abstract contract — never on a concrete
provider.

A provider must implement:
- ``enabled``        — whether the provider is configured and usable now
- ``generate_json``  — return a JSON-decoded object for a system+user
                       prompt pair (used by the structured AI features)
- ``chat``           — return plain text for a system+user prompt pair
- ``generate``       — alias of ``chat`` (free-text generation)
- ``health_check``   — report provider availability / latency / version

Adding a new provider (Ollama, OpenAI, Claude, Azure OpenAI) requires:
1. implementing ``BaseLLMProvider`` in a sibling module,
2. registering it in ``LLMProviderFactory`` (``factory.py``).
No business-logic changes are required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.exceptions.gemini_exceptions import LLMProviderError


class BaseLLMProvider(ABC):
    """Common interface implemented by every LLM provider."""

    #: Stable provider name, e.g. ``"ollama"`` or ``"gemini"``.
    name: str = "base"
    #: Active model identifier (reported by health checks / logging).
    model: str = ""

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """True when the provider is configured and usable."""

    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """Return a JSON-decoded object from the provider.

        Parameters
        ----------
        system_prompt:
            The model's system instruction (role/constraints).
        user_prompt:
            The concrete request content.

        Returns
        -------
        dict
            A parsed JSON object.

        Raises
        ------
        LLMProviderError
            A provider-specific subclass on any failure (timeout,
            network, quota, or malformed response).  Callers catch the
            base type to fall back gracefully.
        """

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Return plain text from the provider.

        Default implementation derives text from :meth:`generate_json`
        (handy for JSON-only providers and test fakes).  Concrete
        providers with a native text path (Ollama, Gemini) override it.

        Raises ``LLMProviderError`` (or a subclass) on any failure.
        """
        data = self.generate_json(system_prompt, user_prompt)
        if isinstance(data, dict):
            for key in ("reply", "response", "summary", "text"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        raise LLMProviderError("Provider returned no usable text reply.")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Free-text generation (alias of :meth:`chat`)."""
        return self.chat(system_prompt, user_prompt)

    def health_check(self) -> Dict[str, Any]:
        """Report provider health.

        Default implementation reports the configured state.  Concrete
        providers should override with a real probe.  **Must never
        raise** — the health endpoint relies on this contract.

        Returns a dict with ``provider``, ``model``, ``status``
        (``ok`` | ``unconfigured`` | ``error`` | ``unavailable``),
        ``latency_ms``, ``version`` and ``detail`` keys.
        """
        return {
            "provider": self.name,
            "model": self.model,
            "status": "ok" if self.enabled else "unconfigured",
            "latency_ms": 0.0,
            "version": None,
            "detail": "",
        }


# Backward-compatible alias: code written against ``LLMClient`` (tests,
# benchmarks, earlier integrations) keeps working unchanged.
LLMClient = BaseLLMProvider
