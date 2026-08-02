"""Integration tests for the AI Dietitian orchestration + cache.

Uses an in-memory database and a fake LLM client so no external API is
called and no ML models are loaded.  Verifies the full
cache-aware flow that the ``analyze_meal`` endpoint relies on:

- successful response (all fields present, health score deterministic)
- cache miss -> LLM called
- cache hit  -> LLM NOT called again
- Gemini disabled -> None (rule-based fallback)
- Gemini timeout -> None (rule-based fallback)
- invalid JSON  -> None (rule-based fallback)
- cache invalidation -> next call re-invokes the LLM
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.database import Base
from backend.exceptions.gemini_exceptions import (
    GeminiParsingError,
    GeminiTimeoutError,
)
from backend.services.llm.base import LLMClient
from backend.services.meal_ai_service import MealAIService


class FakeLLMClient(LLMClient):
    """Deterministic stand-in for the Gemini client."""

    def __init__(self, *, enabled: bool = True, result=None, error=None) -> None:
        self._enabled = enabled
        self._result = result or {
            "summary": "A balanced vegetarian meal.",
            "meal_quality": "Good",
            "risk_explanation": "Low risk across all dimensions.",
            "recommendations": ["Add fiber"],
            "healthier_alternatives": ["Brown rice instead of white"],
            "warnings": ["Sodium is moderate"],
            "follow_up_questions": ["Would you like dinner ideas?"],
        }
        self._error = error
        self.calls = 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        self.calls += 1
        if self._error:
            raise self._error
        return self._result


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


ARGS = dict(
    foods=[
        {
            "name": "Vegetable samosa",
            "display_name": "Samosa",
            "weight_g": 100,
            "calories": 97,
            "protein": 2.0,
            "carbs": 10.0,
            "fats": 5.0,
        }
    ],
    nutrition={
        "calories": 97.0,
        "protein": 2.0,
        "carbs": 10.0,
        "fats": 5.0,
        "sodium": 300.0,
        "sugar": 3.0,
        "fiber": 1.0,
    },
    dci=0.8,
    dci_level="High Consistency",
    nis=0.3,
    nis_level="Mild Imbalance",
    predictions={
        "diabetes_risk": 0.2,
        "obesity_risk": 0.3,
        "hypertension_risk": 0.1,
        "deficiency_risk": 0.2,
    },
    fusion={"fused_score": 0.25, "risk_level": "Low"},
    rule_recommendations=[{"category": "General", "content": "Eat well"}],
    user_profile={"age": 30, "gender": "Male"},
)


class TestSuccessfulResponse:
    def test_all_fields_present_and_health_score_deterministic(self, db):
        client = FakeLLMClient()
        service = MealAIService(client=client)
        result = service.analyze_meal_cached(
            db,
            meal_id=1,
            provider="gemini",
            model="gemini-2.0-flash",
            **ARGS,
        )
        assert result is not None
        assert result["summary"] == "A balanced vegetarian meal."
        assert result["meal_quality"] == "Good"
        assert isinstance(result["health_score"], int)
        assert 0 <= result["health_score"] <= 100
        assert result["health_level"] in (
            "Excellent", "Good", "Moderate", "Needs improvement",
        )
        assert result["health_explanation"]
        assert result["recommendations"] == ["Add fiber"]
        assert result["healthier_alternatives"] == ["Brown rice instead of white"]
        assert result["warnings"] == ["Sodium is moderate"]
        assert result["follow_up_questions"] == ["Would you like dinner ideas?"]
        assert client.calls == 1


class TestCache:
    def test_cache_miss_then_hit_no_second_llm_call(self, db):
        client = FakeLLMClient()
        service = MealAIService(client=client)

        first = service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert first is not None
        assert client.calls == 1  # miss -> LLM called

        second = service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert second == first          # identical response
        assert client.calls == 1        # hit -> LLM NOT called again

    def test_cache_isolation_by_context(self, db):
        client = FakeLLMClient()
        service = MealAIService(client=client)

        service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        # Same meal_id but different nutrition -> different context hash
        changed = {**ARGS, "nutrition": {**ARGS["nutrition"], "calories": 900.0}}
        service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **changed,
        )
        assert client.calls == 2  # second context was a cache miss

    def test_invalidation_causes_re_invocation(self, db):
        client = FakeLLMClient()
        service = MealAIService(client=client)

        service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert client.calls == 1

        # Invalidate the cache row, then run again.
        deleted = service._cache.invalidate(db, meal_id=1)
        assert deleted == 1

        service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert client.calls == 2  # re-invoked after invalidation


class TestFailureModes:
    def test_gemini_disabled_returns_none(self, db):
        client = FakeLLMClient(enabled=False)
        service = MealAIService(client=client)
        result = service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert result is None
        assert client.calls == 0

    def test_gemini_timeout_returns_none(self, db):
        client = FakeLLMClient(error=GeminiTimeoutError("timed out"))
        service = MealAIService(client=client)
        result = service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert result is None
        assert client.calls == 1  # attempted once

    def test_invalid_json_returns_none(self, db):
        client = FakeLLMClient(error=GeminiParsingError("bad json"))
        service = MealAIService(client=client)
        result = service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        assert result is None
        assert client.calls == 1

    def test_failure_does_not_cache_nothing(self, db):
        client = FakeLLMClient(error=GeminiTimeoutError("timed out"))
        service = MealAIService(client=client)
        service.analyze_meal_cached(
            db, meal_id=1, provider="gemini", model="m", **ARGS,
        )
        # Nothing should have been persisted on failure.
        assert service._cache.get_cached_response(
            db, context_hash=service._cache.context_hash(
                service.build_context(**ARGS)
            )
        ) is None
