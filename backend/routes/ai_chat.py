"""AI Dietitian chat endpoint.

``POST /api/ai/chat`` — answers a meal-specific question using the
existing meal analysis as context.  No ML is re-run; only the LLM
provider is invoked.

Error handling: Gemini timeouts / quota / missing key / parsing failures
return a friendly reply with HTTP 200.  Only genuine request problems
(empty message, meal not owned by the user) return 4xx.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.routes.deps import get_current_user
from backend.services.chat_ai_service import (
    MealNotFoundError,
    chat_ai_service,
)
from backend.services.llm.factory import get_llm_client
from backend.utils.logger import api_logger

router = APIRouter(prefix="", tags=["AI Dietitian"])

# Friendly message shown when the LLM provider is unavailable.
UNAVAILABLE_REPLY = (
    "The AI Dietitian is temporarily unavailable. "
    "Please try again in a moment."
)


class ChatRequest(BaseModel):
    meal_id: int
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    reply: str


@router.post("/ai/chat", response_model=ChatResponse)
def ai_chat(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    message = data.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty.",
        )

    try:
        reply = chat_ai_service.chat(
            db,
            user_id=current_user.id,
            meal_id=data.meal_id,
            message=message,
        )
    except MealNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meal not found for the current user.",
        )
    except LLMProviderError as exc:
        # Never fail the request because of the LLM provider.  The full
        # exception is logged server-side for debugging; only the friendly
        # message reaches the client (no secrets, paths or provider
        # internals are exposed).
        api_logger.warning(
            "AI chat unavailable (%s): %s; returning friendly message.",
            type(exc).__name__,
            exc,
        )
        return {"reply": UNAVAILABLE_REPLY}

    return {"reply": reply}


@router.get("/ai/health")
def ai_provider_health() -> dict:
    """Report the health of the configured LLM provider.

    Returns the active provider, model, status, latency and version.
    Never raises — provider failures are reported in the payload.
    """
    provider = get_llm_client()
    try:
        return provider.health_check()
    except Exception as exc:  # noqa: BLE001 — health endpoint never 500s
        api_logger.error("AI health check failed: %s", exc)
        return {
            "provider": getattr(provider, "name", "unknown"),
            "model": getattr(provider, "model", ""),
            "status": "error",
            "latency_ms": 0.0,
            "version": None,
            "detail": str(exc)[:200],
        }
