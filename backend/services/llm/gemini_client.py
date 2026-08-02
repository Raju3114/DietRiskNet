"""Gemini LLM provider (optional cloud provider) — pure API client.

Responsibilities — ONLY transport:
- Gemini SDK initialisation and authentication
- API communication
- Timeout handling
- Retry with backoff on transient failures
- JSON parsing / code-fence stripping
- Typed error handling

This module intentionally contains NO business logic about meals,
health scores, or prompts.  Orchestration lives in
``meal_ai_service``; prompt text lives in ``backend/prompts``.

Implements the ``BaseLLMProvider`` interface, so it can be swapped with
``OllamaProvider`` (the default local provider) or any future provider
through ``LLMProviderFactory``.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, Optional

from backend.config import settings
from backend.exceptions.gemini_exceptions import (
    GeminiParsingError,
    GeminiTimeoutError,
    GeminiUnavailableError,
    LLMProviderError,
)
from backend.services.llm.base import BaseLLMProvider
from backend.utils.logger import app_logger

# Total attempts including the first call.
MAX_ATTEMPTS = 2
# Backoff base (seconds) between retries; scaled by attempt number.
RETRY_BACKOFF_SECONDS = 1.0


class GeminiProvider(BaseLLMProvider):
    """Concrete LLM provider backed by Google's Gemini API."""

    name = "gemini"

    def __init__(self) -> None:
        self._api_key: str = settings.GEMINI_API_KEY or ""
        self._enabled: bool = bool(self._api_key)
        self._model: Any = None

    @property
    def model(self) -> str:
        return settings.GEMINI_MODEL

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ------------------------------------------------------------------
    # BaseLLMProvider API
    # ------------------------------------------------------------------

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        if not self._enabled:
            raise GeminiUnavailableError(
                "Gemini is not configured (GEMINI_API_KEY is empty)."
            )

        model = self._get_model(system_prompt)
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                raw = self._generate(model, user_prompt)
                return self._parse_json(raw)
            except GeminiParsingError:
                # Malformed content will not improve on retry.
                raise
            except GeminiUnavailableError as exc:
                last_error = exc
                if attempt < MAX_ATTEMPTS and self._is_retryable(exc):
                    delay = RETRY_BACKOFF_SECONDS * attempt
                    app_logger.warning(
                        "gemini attempt=%d/%d failed (%s); retrying in %.1fs",
                        attempt, MAX_ATTEMPTS, type(exc).__name__, delay,
                    )
                    time.sleep(delay)

        raise GeminiUnavailableError(
            "Gemini request failed after retries.", cause=last_error
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self._enabled:
            raise GeminiUnavailableError(
                "Gemini is not configured (GEMINI_API_KEY is empty)."
            )
        model = self._get_model(system_prompt)
        text = self._generate_text(model, user_prompt)
        return text.strip()

    def health_check(self) -> Dict[str, Any]:
        """Probe the provider with a short, single-shot generation.

        Must never raise (the health endpoint relies on this).
        """
        if not self._enabled:
            return {
                "provider": self.name,
                "model": self.model,
                "status": "unconfigured",
                "latency_ms": 0.0,
                "version": None,
                "detail": "GEMINI_API_KEY is not set.",
            }
        started = time.perf_counter()
        try:
            self._probe()
            status = "ok"
            detail = ""
        except LLMProviderError as exc:
            status = "error"
            detail = str(exc)[:200]
        return {
            "provider": self.name,
            "model": self.model,
            "status": status,
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 1),
            "version": self.model,
            "detail": detail,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_model(self, system_prompt: str) -> Any:
        """Lazily build the GenerativeModel.  Imported lazily so the
        backend can still start if the SDK is not installed."""
        if self._model is not None:
            return self._model
        try:
            import google.generativeai as genai  # local import

            genai.configure(api_key=self._api_key)
            self._model = genai.GenerativeModel(
                settings.GEMINI_MODEL,
                system_instruction=system_prompt,
            )
            app_logger.info(
                "gemini client initialised (model=%s)", settings.GEMINI_MODEL,
            )
        except Exception as exc:
            raise GeminiUnavailableError(
                "Failed to initialise Gemini client.", cause=exc
            )
        return self._model

    def _generate(self, model: Any, user_prompt: str) -> str:
        """Send one JSON request and return the raw text response."""
        try:
            import google.generativeai as genai  # local import

            response = model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
                request_options={"timeout": settings.GEMINI_TIMEOUT_SECONDS},
            )
        except Exception as exc:
            raise self._map_sdk_error(exc)

        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise GeminiUnavailableError("Gemini returned an empty response.")
        return text

    def _generate_text(self, model: Any, user_prompt: str) -> str:
        """Send one plain-text request and return the raw text."""
        try:
            import google.generativeai as genai  # local import

            response = model.generate_content(
                user_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.3),
                request_options={"timeout": settings.GEMINI_TIMEOUT_SECONDS},
            )
        except Exception as exc:
            raise self._map_sdk_error(exc)

        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise GeminiUnavailableError("Gemini returned an empty response.")
        return text

    def _probe(self) -> None:
        """One short-lived generation used by ``health_check`` (no retries)."""
        model = self._get_model("Reply with JSON only.")
        try:
            import google.generativeai as genai  # local import

            model.generate_content(
                '{"ok": true}',
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
                request_options={
                    "timeout": min(settings.GEMINI_TIMEOUT_SECONDS, 5.0)
                },
            )
        except Exception as exc:
            raise self._map_sdk_error(exc)

    @staticmethod
    def _map_sdk_error(exc: Exception) -> GeminiUnavailableError:
        name = type(exc).__name__
        lowered = name.lower()
        if "deadline" in lowered or "timeout" in lowered:
            return GeminiTimeoutError("Gemini request timed out.", cause=exc)
        return GeminiUnavailableError(f"Gemini API error: {name}", cause=exc)

    @staticmethod
    def _is_retryable(exc: GeminiUnavailableError) -> bool:
        # Only retry timeouts; parsing errors and quota/confirmation
        # errors should surface immediately to the caller.
        return isinstance(exc, GeminiTimeoutError)

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Decode the model response, stripping code fences if present."""
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiParsingError("Gemini returned invalid JSON.", cause=exc)

        if not isinstance(data, dict):
            raise GeminiParsingError(
                "Gemini returned JSON that is not an object."
            )
        return data


# Backward-compatible alias: code written against ``GeminiClient``
# (factory, tests) keeps working unchanged.
GeminiClient = GeminiProvider
