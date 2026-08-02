"""General-purpose AI Nutrition Assistant.

Unlike the meal-specific AI chat, this assistant answers general
nutrition, meal-planning, and dietary-guidance questions and works even
when the user has analysed no meal.

When the user has meal history, the service reads the PERSISTED analysis
(recent foods, nutrition, DCI, NIS, disease risks) from the database and
includes it in the context — it NEVER re-runs YOLO, EfficientNet,
nutrition, or prediction.

Reuses:
- ``BaseLLMProvider`` abstraction (Ollama by default, Gemini optional)
- ``ConversationStore`` for rolling in-memory history
- typed ``LLMProviderError`` failure handling
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.database.models import Meal, User
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.services.conversation_store import ConversationStore
from backend.services.llm.base import BaseLLMProvider
from backend.services.llm.factory import get_llm_client
from backend.services.nutrition_analytics_service import (
    nutrition_analytics_service,
)
from backend.utils.logger import app_logger

# Rolling window size for the assistant conversation.
MAX_HISTORY_MESSAGES = 10
# How many recent meals to summarise into the context.
RECENT_MEALS_LIMIT = 5

# Polite reply used when the user strays outside nutrition topics.
OUT_OF_SCOPE_REPLY = (
    "I'm DietRiskNet's AI Nutrition Assistant. I specialize in nutrition, "
    "healthy eating, food, meal planning, and dietary guidance."
)

# Conservative keyword guard for the most obvious off-topic domains.
_OFF_TOPIC_KEYWORDS = (
    "politics", "election", "vote", "government",
    "programming", "coding", "python", "javascript", "software",
    "movie", "film", "hollywood",
    "sports team", "cricket score", "football match",
    "homework", "math problem", "history essay",
)

# Prompt text, loaded once from the template file.
_SYSTEM_PROMPT: Optional[str] = None
_USER_TEMPLATE: Optional[str] = None
_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "prompts", "nutrition_assistant_prompt.txt"
)


def _load_prompts() -> None:
    global _SYSTEM_PROMPT, _USER_TEMPLATE
    if _SYSTEM_PROMPT is not None:
        return
    with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    sys_marker = content.find("[SYSTEM]")
    usr_marker = content.find("[USER]")
    _SYSTEM_PROMPT = content[sys_marker + len("[SYSTEM]"): usr_marker].strip()
    _USER_TEMPLATE = content[usr_marker + len("[USER]"):].strip()


class NutritionAssistantService:
    """Answers general nutrition questions via the LLM provider."""

    def __init__(
        self,
        client: Optional[BaseLLMProvider] = None,
        store: Optional[ConversationStore] = None,
    ) -> None:
        _load_prompts()
        self._client: BaseLLMProvider = client or get_llm_client()
        self._store: ConversationStore = store or ConversationStore(
            max_messages=MAX_HISTORY_MESSAGES
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        db: Session,
        *,
        user_id: int,
        message: str,
        include_history: bool = True,
    ) -> str:
        """Answer a general nutrition question for *user_id*.

        Raises ``LLMProviderError`` when the provider is disabled or
        fails; the caller maps it to a friendly reply.
        """
        # Fast, deterministic out-of-scope guard (no LLM call needed).
        if self._is_off_topic(message):
            app_logger.debug("nutrition assistant: off-topic question blocked")
            return OUT_OF_SCOPE_REPLY

        if not self._client.enabled:
            raise LLMProviderError("LLM provider is not configured.")

        session = self._store.get_or_create(user_id)
        if session.data is None:
            session.data = self._build_user_context(
                db, user_id, include_history=include_history
            )

        prompt = self._build_prompt(session.data, session.history, message)
        app_logger.debug("nutrition assistant prompt length=%d", len(prompt))

        # Plain-text generation: the assistant's reply is conversational,
        # so we do NOT force the provider into `format:"json"`.  This
        # avoids exposing raw JSON to the UI and removes JSON-schema
        # generation overhead for short replies (better U-layer latency).
        reply = (self._client.chat(_SYSTEM_PROMPT, prompt) or "").strip()
        if not reply:
            reply = "I could not generate an answer for that question."
        self._store.append(user_id, message, reply)
        return reply

    # ------------------------------------------------------------------
    # Context / prompt
    # ------------------------------------------------------------------

    @staticmethod
    def build_user_context(db: Session, user_id: int) -> Dict[str, Any]:
        """Build a personalised context from stored user + meal data."""
        user = db.query(User).filter(User.id == user_id).first()

        profile: Dict[str, Any] = {}
        if user is not None and user.settings is not None:
            profile = {
                "age": user.settings.age,
                "gender": user.settings.gender,
                "height_cm": user.settings.height,
                "weight_kg": user.settings.weight,
                "activity_level": user.settings.activity_level,
                "existing_conditions": user.settings.existing_conditions or [],
            }

        meals = (
            db.query(Meal)
            .filter(Meal.user_id == user_id)
            .order_by(Meal.created_at.desc())
            .limit(RECENT_MEALS_LIMIT)
            .all()
        )
        recent = []
        for meal in meals:
            recent.append({
                "logged": (
                    meal.created_at.strftime("%Y-%m-%d %H:%M")
                    if meal.created_at else None
                ),
                "foods": [item.name for item in meal.items],
                "calories": meal.nutrition.calories if meal.nutrition else None,
                "dci": meal.dci,
                "nis": meal.nis,
                "diabetes_risk": meal.predictions.diabetes_risk if meal.predictions else None,
                "obesity_risk": meal.predictions.obesity_risk if meal.predictions else None,
                "hypertension_risk": meal.predictions.hypertension_risk if meal.predictions else None,
                "deficiency_risk": meal.predictions.deficiency_risk if meal.predictions else None,
            })

        analytics = nutrition_analytics_service.compute_analytics(db, user_id)
        return {
            "user_profile": profile,
            "recent_meals": recent,
            "coach_summary": nutrition_analytics_service.summary_for_context(
                analytics
            ),
        }

    def _build_user_context(
        self,
        db: Session,
        user_id: int,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        context = self.build_user_context(db, user_id)
        if not include_history:
            # Start a context that does not reference stored meals.
            context["recent_meals"] = []
            context["coach_summary"] = "The user has no analysed meals yet."
        return context

    # ------------------------------------------------------------------
    # Coach analytics (used by the dashboard / proactive insights)
    # ------------------------------------------------------------------

    def get_analytics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Return deterministic dietary analytics for the user.

        Aggregates stored meal history only — no ML re-run, no LLM call.
        """
        return nutrition_analytics_service.compute_analytics(db, user_id)

    def _build_prompt(
        self,
        context: Dict[str, Any],
        history: list,
        question: str,
    ) -> str:
        context_json = json.dumps(context, indent=2, ensure_ascii=False)
        history_json = json.dumps(history, ensure_ascii=False) if history else "[]"
        return _USER_TEMPLATE.format(
            context_json=context_json,
            history_json=history_json,
            question=question,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_off_topic(message: str) -> bool:
        lowered = message.lower().strip()
        return any(kw in lowered for kw in _OFF_TOPIC_KEYWORDS)

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
nutrition_assistant_service = NutritionAssistantService()
