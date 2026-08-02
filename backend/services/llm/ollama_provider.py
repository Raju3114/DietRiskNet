"""Ollama LLM provider — the default LOCAL provider.

Talks to a locally installed Ollama server over its REST API
(``/api/generate``, ``/api/version``, ``/api/tags``).  No API key is
required — the application works fully offline with a local model such
as ``llama3.2:3b``.

Endpoint / model / timeout are configured via settings:
``OLLAMA_URL``, ``OLLAMA_MODEL``, ``OLLAMA_TIMEOUT``.

Failure behaviour: any transport / HTTP / parsing error is raised as an
``LLMProviderError`` (or subclass), which the AI services catch and
translate into the existing graceful fallback (never an HTTP 500).
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

import httpx

from backend.config import settings
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.services.llm.base import BaseLLMProvider
from backend.utils.logger import app_logger


class OllamaProvider(BaseLLMProvider):
    """Concrete LLM provider backed by a local Ollama server."""

    name = "ollama"

    def __init__(
        self,
        url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self._url: str = (url or settings.OLLAMA_URL).rstrip("/")
        self._model: str = model or settings.OLLAMA_MODEL
        self._timeout: float = (
            timeout if timeout is not None else settings.OLLAMA_TIMEOUT
        )

    @property
    def model(self) -> str:
        return self._model

    @property
    def enabled(self) -> bool:
        # Ollama is a local provider — no key required.  ``enabled``
        # reports that the provider is *configured*; actual reachability
        # is probed lazily in generate/chat and surfaced by
        # ``health_check``.
        return True

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(f"{self._url}{path}", json=payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Ollama HTTP {exc.response.status_code} for {path}: "
                f"{exc.response.text[:200]}",
                cause=exc,
            )
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                f"Ollama request timed out after {self._timeout:.0f}s ({path}).",
                cause=exc,
            )
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"Ollama request failed ({path}): {exc}", cause=exc
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise LLMProviderError(
                f"Ollama returned a non-JSON response for {path}.", cause=exc
            )

    def _get(self, path: str) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(f"{self._url}{path}")
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMProviderError(
                f"Ollama HTTP {exc.response.status_code} for {path}.", cause=exc
            )
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                f"Ollama request timed out after {self._timeout:.0f}s ({path}).",
                cause=exc,
            )
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"Ollama request failed ({path}): {exc}", cause=exc
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise LLMProviderError(
                f"Ollama returned a non-JSON response for {path}.", cause=exc
            )

    # ------------------------------------------------------------------
    # BaseLLMProvider API
    # ------------------------------------------------------------------

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        data = self._post(
            "/api/generate",
            {
                "model": self._model,
                "system": system_prompt or "",
                "prompt": user_prompt,
                "stream": False,
                "format": "json",
            },
        )
        text = data.get("response", "").strip()
        if not text:
            raise LLMProviderError("Ollama returned an empty response.")
        return self._parse_json(text)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        data = self._post(
            "/api/generate",
            {
                "model": self._model,
                "system": system_prompt or "",
                "prompt": user_prompt,
                "stream": False,
                # Bound generation length for the conversational reply path
                # (chat answers should be concise).  Structured JSON
                # generation (generate_json) is deliberately not capped.
                "options": {"num_predict": 200},
            },
        )
        reply = data.get("response", "").strip()
        if not reply:
            raise LLMProviderError("Ollama returned an empty response.")
        return reply

    def health_check(self) -> Dict[str, Any]:
        started = time.perf_counter()
        try:
            version_data = self._get("/api/version")
            tags = self._get("/api/tags")
        except LLMProviderError as exc:
            app_logger.warning("Ollama health check failed: %s", exc)
            return {
                "provider": self.name,
                "model": self._model,
                "status": "unavailable",
                "latency_ms": round((time.perf_counter() - started) * 1000.0, 1),
                "version": None,
                "detail": str(exc),
            }

        installed = [m.get("name") for m in tags.get("models", []) if m.get("name")]
        return {
            "provider": self.name,
            "model": self._model,
            "status": "ok",
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 1),
            "version": version_data.get("version"),
            "detail": (
                "model_installed" if self._model in installed
                else f"model_not_installed; available: {', '.join(sorted(installed)) or 'none'}"
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        # Strip optional code fences.
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
            cleaned = cleaned.removesuffix("```").strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Locate the first JSON object in the response text.
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end > start:
                try:
                    data = json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError as exc:
                    raise LLMProviderError(
                        "Ollama returned content that is not valid JSON.", cause=exc
                    )
            else:
                raise LLMProviderError(
                    "Ollama returned content that is not valid JSON."
                )
        if not isinstance(data, dict):
            raise LLMProviderError("Ollama returned JSON that is not an object.")
        return data


# Convenience singleton (matches the project's service pattern).
ollama_provider = OllamaProvider()
