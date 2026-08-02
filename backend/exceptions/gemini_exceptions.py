"""Typed exceptions for LLM-powered features (currently Gemini).

The hierarchy separates *cause* from *recovery*:

- ``LLMProviderError``      -> base class shared by every LLM provider
  (Gemini today; OpenAI / Claude / Ollama / Azure OpenAI later).
  The orchestration layer catches this base type, so adding a new
  provider never changes business logic.
- ``GeminiUnavailableError``-> the Gemini API could not be reached, the
  key is missing, or the API returned a non-recoverable error.  Callers
  fall back to the rule-based recommendation engine.
- ``GeminiTimeoutError``     -> the request exceeded the configured
  timeout.  Subclass of ``GeminiUnavailableError`` so callers can catch
  it broadly or specifically.
- ``GeminiParsingError``     -> Gemini responded, but the content was not
  valid JSON or did not match the expected shape.  Subclass of
  ``GeminiUnavailableError`` so the same fallback path applies.

Every exception carries an optional ``cause`` so the caller can log the
underlying error without exposing the API key or the full prompt.
"""


class LLMProviderError(Exception):
    """Base class for all LLM provider failures.

    Attributes:
        message: Human-readable description safe to log.
        cause:   The original exception (if any), kept for diagnostics.
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class GeminiUnavailableError(LLMProviderError):
    """Raised when the Gemini API is unavailable or returns a fatal error."""


class GeminiTimeoutError(GeminiUnavailableError):
    """Raised when a Gemini request exceeds the configured timeout."""


class GeminiParsingError(GeminiUnavailableError):
    """Raised when Gemini returns content that cannot be parsed as JSON."""
