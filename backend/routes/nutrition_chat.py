"""AI Nutrition Assistant endpoint.

``POST /api/nutrition-chat`` — answers general nutrition / meal-planning
/ dietary questions. Works with or without a meal analysis, and can
optionally include the user's recent meal history for personalisation.

Error handling: LLM failures (timeout / quota / missing key / parsing)
return a friendly reply with HTTP 200 — never a 500.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.routes.deps import get_current_user
from backend.services.nutrition_assistant_service import (
    nutrition_assistant_service,
)
from backend.utils.logger import api_logger

router = APIRouter(prefix="", tags=["AI Nutrition Assistant"])

UNAVAILABLE_REPLY = (
    "The AI Nutrition Assistant is temporarily unavailable. "
    "Please try again in a moment."
)


class NutritionChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    include_history: bool = True


class NutritionChatResponse(BaseModel):
    reply: str


@router.post("/nutrition-chat", response_model=NutritionChatResponse)
def nutrition_chat(
    data: NutritionChatRequest,
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
        reply = nutrition_assistant_service.chat(
            db,
            user_id=current_user.id,
            message=message,
            include_history=data.include_history,
        )
    except LLMProviderError as exc:
        # Never fail the request because of the LLM provider.  The full
        # exception is logged server-side for debugging; only the friendly
        # message reaches the client (no secrets, paths or provider
        # internals are exposed).
        api_logger.warning(
            "AI Nutrition Assistant unavailable (%s): %s; returning friendly message.",
            type(exc).__name__,
            exc,
        )
        return {"reply": UNAVAILABLE_REPLY}

    return {"reply": reply}
