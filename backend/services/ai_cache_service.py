"""Persistent AI Dietitian result cache.

A thin repository over ``AIDietitianResult`` that stores / retrieves /
invalidates LLM results keyed by a stable ``context_hash``.

Cache key semantics
-------------------
``context_hash`` is derived from the FULL structured context sent to the
LLM: foods, nutrition, DCI, NIS, disease predictions, fusion score,
rule-based recommendations, and user profile.  If none of those change,
Gemini (or any provider) is never called again.

Provider-agnostic
-----------------
The cache is keyed by ``(context_hash, provider)``.  Results from
different providers (Gemini, Claude, OpenAI, Ollama) coexist without any
schema change.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database.models import AIDietitianResult
from backend.utils.logger import db_logger

# Bump when the prompt or context schema changes meaningfully, so stale
# cached responses are not served against a new prompt.
PROMPT_VERSION = "1"


class AICacheService:
    """Repository for ``AIDietitianResult`` rows."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def context_hash(context: Dict[str, Any]) -> str:
        """Return a stable SHA-256 hash of a context dict.

        ``sort_keys=True`` + ``default=str`` make the hash insensitive to
        dict insertion order and tolerant of non-JSON values (e.g. numpy
        floats), so identical contexts always hash identically.
        """
        blob = json.dumps(
            context,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def save_response(
        self,
        db: Session,
        *,
        meal_id: int,
        provider: str,
        model: Optional[str],
        context: Dict[str, Any],
        response: Dict[str, Any],
        prompt_version: str = PROMPT_VERSION,
    ) -> AIDietitianResult:
        """Persist one LLM result for *meal_id*.

        ``response`` is a plain dict with the fields described in
        ``AIDietitianResult`` (summary, meal_quality, health_score,
        risk_explanation, recommendations, healthier_alternatives,
        warnings, follow_up_questions).
        """
        row = AIDietitianResult(
            meal_id=meal_id,
            provider=provider,
            model=model,
            summary=response.get("summary"),
            meal_quality=response.get("meal_quality"),
            health_score=response.get("health_score"),
            health_level=response.get("health_level"),
            health_explanation=response.get("health_explanation"),
            risk_explanation=response.get("risk_explanation"),
            recommendations_json=response.get("recommendations", []),
            alternatives_json=response.get("healthier_alternatives", []),
            warnings_json=response.get("warnings", []),
            follow_up_questions_json=response.get("follow_up_questions", []),
            prompt_version=prompt_version,
            context_hash=self.context_hash(context),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        db_logger.info(
            "AI result cached (meal_id=%s provider=%s hash=%s…)",
            meal_id, provider, row.context_hash[:12],
        )
        return row

    def get_cached_response(
        self,
        db: Session,
        *,
        context_hash: str,
        provider: Optional[str] = None,
        prompt_version: str = PROMPT_VERSION,
    ) -> Optional[AIDietitianResult]:
        """Return the latest cached result for a context hash, if any.

        ``provider`` narrows the lookup to one provider (default: any).
        A mismatch in ``prompt_version`` invalidates the cache logically.
        """
        query = db.query(AIDietitianResult).filter(
            AIDietitianResult.context_hash == context_hash,
            AIDietitianResult.prompt_version == prompt_version,
        )
        if provider:
            query = query.filter(AIDietitianResult.provider == provider)

        row = query.order_by(AIDietitianResult.created_at.desc()).first()
        if row is not None:
            db_logger.debug("AI cache hit (hash=%s…)", context_hash[:12])
        return row

    @staticmethod
    def to_response_dict(row: AIDietitianResult) -> Dict[str, Any]:
        """Convert a stored cache row back into the API response shape.

        Keys match ``AIDietitianResponse`` so a cache hit can be
        returned directly without re-invoking the LLM.
        """
        return {
            "summary": row.summary,
            "meal_quality": row.meal_quality,
            "health_score": row.health_score,
            "health_level": row.health_level,
            "health_explanation": row.health_explanation,
            "risk_explanation": row.risk_explanation,
            "recommendations": row.recommendations_json or [],
            "healthier_alternatives": row.alternatives_json or [],
            "warnings": row.warnings_json or [],
            "follow_up_questions": row.follow_up_questions_json or [],
        }

    def invalidate(
        self,
        db: Session,
        *,
        meal_id: Optional[int] = None,
        context_hash: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> int:
        """Delete matching cache rows.  Returns the number deleted.

        At least one of ``meal_id`` / ``context_hash`` must be provided.
        """
        query = db.query(AIDietitianResult)
        if meal_id is not None:
            query = query.filter(AIDietitianResult.meal_id == meal_id)
        if context_hash is not None:
            query = query.filter(AIDietitianResult.context_hash == context_hash)
        if provider is not None:
            query = query.filter(AIDietitianResult.provider == provider)

        deleted = query.delete(synchronize_session=False)
        db.commit()
        db_logger.info("AI cache invalidated: %d row(s) deleted", deleted)
        return deleted


# Singleton for convenience (matches the project's service pattern).
ai_cache_service = AICacheService()
