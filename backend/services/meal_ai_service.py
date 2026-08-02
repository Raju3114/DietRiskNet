"""AI Dietitian orchestration layer.

Consumes the structured output of the existing ML pipeline and returns a
validated ``AIDietitianResponse``.

Responsibilities:
- Build the AI context from foods / nutrition / DCI / NIS / predictions /
  fusion / rule recommendations / user profile.
- Compute the deterministic health score via ``health_score_service``.
- Check the persistent cache (``ai_cache_service``) — on a hit, never
  call the LLM again.
- On a miss, call the configured LLM provider through the
  ``BaseLLMProvider`` abstraction and persist the result.
- Validate the provider response.

This module has NO HTTP / FastAPI code, so it can be unit tested in
isolation.

Failure mode: if the LLM provider is disabled, errors, or times out,
``analyze_meal_cached`` returns ``None``.  Callers then fall back to the
rule-based engine — the application never fails because the LLM is
unavailable.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.prompts.dietitian_prompt import SYSTEM_PROMPT, build_user_prompt
from backend.services.ai_cache_service import AICacheService, ai_cache_service
from backend.services.health_score_service import compute_health_score
from backend.services.llm.base import BaseLLMProvider
from backend.services.llm.factory import get_llm_client
from backend.utils.logger import app_logger


@dataclass
class AIDietitianResponse:
    """Structured result returned to the caller / API layer.

    ``health_score`` / ``health_level`` / ``health_explanation`` are
    computed deterministically by the backend.  The remaining fields are
    produced by the LLM and validated by ``MealAIService``.
    """

    summary: str
    meal_quality: str
    health_score: int
    health_level: str
    health_explanation: str
    risk_explanation: str
    recommendations: List[str] = field(default_factory=list)
    healthier_alternatives: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)


class MealAIService:
    """Orchestrates the AI Dietitian for a single meal analysis."""

    def __init__(
        self,
        client: Optional[BaseLLMProvider] = None,
        cache: Optional[AICacheService] = None,
    ) -> None:
        self._client: BaseLLMProvider = client or get_llm_client()
        self._cache: AICacheService = cache or ai_cache_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_context(
        self,
        *,
        foods: List[Dict[str, Any]],
        nutrition: Dict[str, float],
        dci: float,
        dci_level: str,
        nis: float,
        nis_level: str,
        predictions: Dict[str, float],
        fusion: Dict[str, Any],
        rule_recommendations: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Assemble the structured context sent to the LLM.

        Only safe, numeric / label data is included: no images, no
        bounding boxes, no tensors, no email / name.
        """
        return {
            "foods": [self._slim_food(item) for item in foods],
            "nutrition": nutrition,
            "dci": {"score": round(float(dci), 4), "level": dci_level},
            "nis": {"score": round(float(nis), 4), "level": nis_level},
            "risk_prediction": {
                "diabetes_risk": round(float(predictions.get("diabetes_risk", 0.0)), 4),
                "obesity_risk": round(float(predictions.get("obesity_risk", 0.0)), 4),
                "hypertension_risk": round(float(predictions.get("hypertension_risk", 0.0)), 4),
                "deficiency_risk": round(float(predictions.get("deficiency_risk", 0.0)), 4),
            },
            "fusion": {
                "fused_score": round(float(fusion.get("fused_score", 0.0)), 4),
                "risk_level": fusion.get("risk_level", "Unknown"),
            },
            "rule_based_recommendations": [
                {
                    "category": rec.get("category", ""),
                    "content": rec.get("content", ""),
                }
                for rec in rule_recommendations
            ],
            "user_profile": user_profile or {},
        }

    def analyze_meal(
        self,
        *,
        foods: List[Dict[str, Any]],
        nutrition: Dict[str, float],
        dci: float,
        dci_level: str,
        nis: float,
        nis_level: str,
        predictions: Dict[str, float],
        fusion: Dict[str, Any],
        rule_recommendations: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Optional[AIDietitianResponse]:
        """Run the AI Dietitian WITHOUT caching.

        Returns ``None`` when the LLM provider is disabled or fails.
        """
        if not self._client.enabled:
            app_logger.info("LLM provider disabled; skipping AI Dietitian.")
            return None

        context = self.build_context(
            foods=foods,
            nutrition=nutrition,
            dci=dci,
            dci_level=dci_level,
            nis=nis,
            nis_level=nis_level,
            predictions=predictions,
            fusion=fusion,
            rule_recommendations=rule_recommendations,
            user_profile=user_profile,
        )
        return self._run_llm(context, dci, nis, fusion, nutrition)

    def analyze_meal_cached(
        self,
        db: Session,
        *,
        meal_id: int,
        provider: str,
        model: str,
        foods: List[Dict[str, Any]],
        nutrition: Dict[str, float],
        dci: float,
        dci_level: str,
        nis: float,
        nis_level: str,
        predictions: Dict[str, float],
        fusion: Dict[str, Any],
        rule_recommendations: List[Dict[str, str]],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Cache-aware AI Dietitian run, returning an API-ready dict.

        Returns ``None`` when the LLM is disabled, unavailable, or the
        run failed — callers then fall back to rule-based output.
        """
        if not self._client.enabled:
            app_logger.info("LLM provider disabled; skipping AI Dietitian.")
            return None

        context = self.build_context(
            foods=foods,
            nutrition=nutrition,
            dci=dci,
            dci_level=dci_level,
            nis=nis,
            nis_level=nis_level,
            predictions=predictions,
            fusion=fusion,
            rule_recommendations=rule_recommendations,
            user_profile=user_profile,
        )
        context_hash = self._cache.context_hash(context)

        # 1. Cache lookup.
        cached = self._cache.get_cached_response(
            db, context_hash=context_hash, provider=provider
        )
        if cached is not None:
            app_logger.info("ai_dietitian cache hit (provider=%s)", provider)
            return self._cache.to_response_dict(cached)

        # 2. Cache miss — call the LLM.
        app_logger.info("ai_dietitian cache miss (provider=%s)", provider)
        start = time.perf_counter()
        result = self._run_llm(context, dci, nis, fusion, nutrition)
        latency_ms = (time.perf_counter() - start) * 1000.0

        if result is None:
            app_logger.warning(
                "ai_dietitian generation failed (provider=%s); falling back",
                provider,
            )
            return None

        # 3. Persist, then return.
        self._cache.save_response(
            db,
            meal_id=meal_id,
            provider=provider,
            model=model,
            context=context,
            response=asdict(result),
        )
        app_logger.info(
            "ai_dietitian generated (provider=%s, latency=%.0fms)",
            provider, latency_ms,
        )
        return asdict(result)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run_llm(
        self,
        context: Dict[str, Any],
        dci: float,
        nis: float,
        fusion: Dict[str, Any],
        nutrition: Dict[str, float],
    ) -> Optional[AIDietitianResponse]:
        """Compute the deterministic health score, call the LLM, validate."""
        health = compute_health_score(
            dci=dci,
            nis=nis,
            fusion_score=fusion.get("fused_score", 0.0),
            nutrition=nutrition,
        )

        prompt = build_user_prompt(context)
        app_logger.debug("ai_dietitian prompt length=%d", len(prompt))

        try:
            raw = self._client.generate_json(SYSTEM_PROMPT, prompt)
        except LLMProviderError as exc:
            app_logger.warning(
                "ai_dietitian unavailable (%s); falling back to rule-based.",
                type(exc).__name__,
            )
            return None

        return self._build_response(raw, health)

    @staticmethod
    def _slim_food(item: Dict[str, Any]) -> Dict[str, Any]:
        """Keep only display-safe fields from a detected food item."""
        return {
            "name": item.get("name"),
            "display_name": item.get("display_name"),
            "weight_g": item.get("weight_g"),
            "calories": item.get("calories"),
            "protein": item.get("protein"),
            "carbs": item.get("carbs"),
            "fats": item.get("fats"),
        }

    @staticmethod
    def _coerce_str(value: Any, default: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return default

    @staticmethod
    def _coerce_list(value: Any, default: Optional[List[str]] = None) -> List[str]:
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return list(default or [])

    def _build_response(
        self,
        raw: Dict[str, Any],
        health: Dict[str, object],
    ) -> AIDietitianResponse:
        """Map the validated LLM JSON onto the response dataclass."""
        return AIDietitianResponse(
            summary=self._coerce_str(raw.get("summary"), "Meal analysis not available."),
            meal_quality=self._coerce_str(raw.get("meal_quality"), "Moderate"),
            health_score=int(health["score"]),
            health_level=str(health["level"]),
            health_explanation=str(health["explanation"]),
            risk_explanation=self._coerce_str(
                raw.get("risk_explanation"),
                "Risk scores were produced by the clinical prediction pipeline.",
            ),
            recommendations=self._coerce_list(raw.get("recommendations")),
            healthier_alternatives=self._coerce_list(
                raw.get("healthier_alternatives")
            ),
            warnings=self._coerce_list(raw.get("warnings")),
            follow_up_questions=self._coerce_list(raw.get("follow_up_questions")),
        )


# Singleton for convenience (matches the project's service pattern).
meal_ai_service = MealAIService()
