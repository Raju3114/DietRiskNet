"""Meal-specific AI Dietitian chat service.

Loads the PERSISTED meal analysis from the database (never recomputes
any ML score), maintains a per-session rolling conversation history
(max 10 messages, in-memory only), and answers via the configured LLM
provider.

No ML inference, no database writes, no image handling.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.database.models import AIDietitianResult, Meal
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.prompts.dietitian_prompt import (
    CHAT_SYSTEM_PROMPT,
    build_chat_prompt,
)
from backend.services.conversation_store import (
    ConversationSession,
    ConversationStore,
)
from backend.services.llm.base import BaseLLMProvider
from backend.services.llm.factory import get_llm_client
from backend.utils.logger import app_logger

# Maximum number of history entries kept per session (rolling window).
MAX_HISTORY_MESSAGES = 10


class MealNotFoundError(Exception):
    """Raised when a meal does not exist or belongs to another user."""


class ChatAIService:
    """Answers meal-specific questions using the LLM provider."""

    def __init__(
        self,
        client: Optional[BaseLLMProvider] = None,
        store: Optional[ConversationStore] = None,
    ) -> None:
        self._client: BaseLLMProvider = client or get_llm_client()
        self._store: ConversationStore = store or ConversationStore(
            max_messages=MAX_HISTORY_MESSAGES
        )

    # Backward-compatible aliases used by callers / tests.
    @property
    def _sessions(self) -> Dict[Any, ConversationStore.sessions]:
        return self._store.sessions

    @property
    def _lock(self) -> Any:
        return self._store._lock

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        db: Session,
        *,
        user_id: int,
        meal_id: int,
        message: str,
    ) -> str:
        """Answer *message* about the meal belonging to *user_id*.

        Raises:
            MealNotFoundError: meal missing or owned by another user.
            LLMProviderError:  provider disabled or failed.
        """
        if not self._client.enabled:
            raise LLMProviderError("LLM provider is not configured.")

        session = self._get_or_create_session(db, user_id, meal_id)

        prompt = build_chat_prompt(
            session.data,
            session.history,
            message,
        )
        app_logger.debug("chat prompt length=%d", len(prompt))

        # Plain-text generation: the meal chat reply is conversational, so
        # we do NOT force the provider into `format:"json"`.  This avoids
        # exposing raw JSON to the UI and removes JSON-schema generation
        # overhead for short replies.
        reply = (self._client.chat(CHAT_SYSTEM_PROMPT, prompt) or "").strip()
        if not reply:
            reply = "I could not generate an answer for that question."

        self._append(user_id, meal_id, message, reply)
        return reply

    @staticmethod
    def build_context_from_meal(
        db: Session,
        user_id: int,
        meal_id: int,
    ) -> Dict[str, Any]:
        """Load the persisted analysis for a meal WITHOUT recomputing.

        Raises MealNotFoundError if the meal does not exist or belongs
        to another user.
        """
        meal = db.query(Meal).filter(Meal.id == meal_id).first()
        if meal is None or meal.user_id != user_id:
            raise MealNotFoundError(
                "Meal not found for the current user."
            )

        nutrition = meal.nutrition
        predictions = meal.predictions
        fusion = meal.fusion_result

        ai_row = (
            db.query(AIDietitianResult)
            .filter(AIDietitianResult.meal_id == meal_id)
            .order_by(AIDietitianResult.created_at.desc())
            .first()
        )

        return {
            "foods": [
                {
                    "name": item.name,
                    "display_name": None,
                    "weight_g": item.weight_g,
                    "calories": item.calories,
                    "protein": item.protein,
                    "carbs": item.carbs,
                    "fats": item.fats,
                }
                for item in meal.items
            ],
            "nutrition": {
                "calories": nutrition.calories if nutrition else 0.0,
                "protein": nutrition.protein if nutrition else 0.0,
                "carbs": nutrition.carbs if nutrition else 0.0,
                "fats": nutrition.fats if nutrition else 0.0,
                "sugar": nutrition.sugar if nutrition else 0.0,
                "fiber": nutrition.fiber if nutrition else 0.0,
                "sodium": nutrition.sodium if nutrition else 0.0,
                "calcium": nutrition.calcium if nutrition else 0.0,
                "iron": nutrition.iron if nutrition else 0.0,
                "vitamin_c": nutrition.vitamin_c if nutrition else 0.0,
                "folate": nutrition.folate if nutrition else 0.0,
            },
            "dci": {"score": meal.dci, "level": meal.dci_level},
            "nis": {"score": meal.nis, "level": meal.nis_level},
            "risk_prediction": {
                "diabetes_risk": predictions.diabetes_risk if predictions else 0.0,
                "obesity_risk": predictions.obesity_risk if predictions else 0.0,
                "hypertension_risk": predictions.hypertension_risk if predictions else 0.0,
                "deficiency_risk": predictions.deficiency_risk if predictions else 0.0,
            },
            "fusion": {
                "fused_score": fusion.fused_score if fusion else 0.0,
                "risk_level": fusion.risk_level if fusion else "Unknown",
            },
            "rule_based_recommendations": [
                {"category": rec.category, "content": rec.content}
                for rec in meal.recommendations
            ],
            "ai_summary": ai_row.summary if ai_row else None,
            "health_score": ai_row.health_score if ai_row else None,
            "health_level": ai_row.health_level if ai_row else None,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_or_create_session(
        self,
        db: Session,
        user_id: int,
        meal_id: int,
    ) -> ConversationSession:
        key = (user_id, meal_id)

        def _factory() -> ConversationSession:
            context = self.build_context_from_meal(db, user_id, meal_id)
            return ConversationSession(data=context)

        return self._store.get_or_create(key, factory=_factory)

    def _append(
        self,
        user_id: int,
        meal_id: int,
        message: str,
        reply: str,
    ) -> None:
        self._store.append((user_id, meal_id), message, reply)

    @staticmethod
    def _extract_reply(raw: Dict[str, Any]) -> str:
        reply = raw.get("reply") or raw.get("summary") or raw.get("response")
        if isinstance(reply, str) and reply.strip():
            return reply.strip()
        if reply is not None and isinstance(reply, (dict, list)):
            return json.dumps(reply, ensure_ascii=False)
        # Robustness for local providers under `format: json`: a small
        # model is non-deterministic about the JSON shape.  Surface the
        # first piece of real content it produced instead of degrading to
        # the generic fallback (never a fabricated answer).
        for value in raw.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, (dict, list)) and value:
                try:
                    return json.dumps(value, ensure_ascii=False)
                except (TypeError, ValueError):
                    return str(value)
            if isinstance(value, (int, float, bool)):
                return str(value)
        return "I could not generate an answer for that question."


# Singleton for convenience (matches the project's service pattern).
chat_ai_service = ChatAIService()
