"""Tests for the persistent AI Dietitian cache.

Covers:
- context hash stability (identical dicts hash identically)
- context hash sensitivity (any input change changes the hash)
- cache miss (empty table returns None)
- cache hit (saved response is retrievable by context hash)
- cache miss when context hash differs
- cache invalidation by meal_id
- cache invalidation by context_hash
- provider isolation (results from different providers coexist)
- prompt_version invalidation (bumped prompt does not hit old cache)
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.database import Base
from backend.database.models import AIDietitianResult
from backend.services.ai_cache_service import ai_cache_service


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


SAMPLE_CONTEXT = {
    "foods": [{"name": "Vegetable samosa", "display_name": "Samosa", "calories": 97}],
    "nutrition": {"calories": 97, "sodium": 300, "sugar": 3, "fiber": 1},
    "dci": {"score": 0.8, "level": "High Consistency"},
    "nis": {"score": 0.3, "level": "Mild Imbalance"},
    "risk_prediction": {
        "diabetes_risk": 0.2,
        "obesity_risk": 0.3,
        "hypertension_risk": 0.1,
        "deficiency_risk": 0.2,
    },
    "fusion": {"fused_score": 0.25, "risk_level": "Low"},
    "rule_based_recommendations": [
        {"category": "General", "content": "Eat a balanced diet."}
    ],
    "user_profile": {"age": 30, "gender": "Male"},
}

SAMPLE_RESPONSE = {
    "summary": "A balanced vegetarian meal.",
    "meal_quality": "Good",
    "health_score": 72,
    "risk_explanation": "Low risk across all dimensions.",
    "recommendations": ["Add fiber"],
    "healthier_alternatives": ["Brown rice instead of white"],
    "warnings": ["Sodium is moderate"],
    "follow_up_questions": ["Would you like dinner ideas?"],
}


class TestContextHash:
    def test_stability(self):
        """Identical dicts must produce identical hashes."""
        h1 = ai_cache_service.context_hash(SAMPLE_CONTEXT)
        h2 = ai_cache_service.context_hash(dict(SAMPLE_CONTEXT))
        assert h1 == h2

    def test_insensitive_to_key_order(self):
        """Key insertion order must not change the hash."""
        a = {"x": 1, "y": 2}
        b = {"y": 2, "x": 1}
        assert ai_cache_service.context_hash(a) == ai_cache_service.context_hash(b)

    def test_nutrition_change_changes_hash(self):
        ctx = dict(SAMPLE_CONTEXT)
        base = ai_cache_service.context_hash(ctx)
        altered = dict(ctx)
        altered["nutrition"] = {**altered["nutrition"], "calories": 500}
        assert ai_cache_service.context_hash(altered) != base

    def test_user_profile_change_changes_hash(self):
        ctx = dict(SAMPLE_CONTEXT)
        base = ai_cache_service.context_hash(ctx)
        altered = dict(ctx)
        altered["user_profile"] = {"age": 55, "gender": "Female"}
        assert ai_cache_service.context_hash(altered) != base

    def test_predictions_change_changes_hash(self):
        ctx = dict(SAMPLE_CONTEXT)
        base = ai_cache_service.context_hash(ctx)
        altered = dict(ctx)
        altered["risk_prediction"] = {**altered["risk_prediction"], "diabetes_risk": 0.9}
        assert ai_cache_service.context_hash(altered) != base


class TestCacheMissHit:
    def test_cache_miss_on_empty(self, db):
        result = ai_cache_service.get_cached_response(
            db, context_hash="nohash"
        )
        assert result is None

    def test_cache_miss_when_hash_differs(self, db):
        ai_cache_service.save_response(
            db,
            meal_id=1,
            provider="gemini",
            model="gemini-2.0-flash",
            context=SAMPLE_CONTEXT,
            response=SAMPLE_RESPONSE,
        )
        # Different context -> different hash -> miss
        other = {**SAMPLE_CONTEXT, "nutrition": {"calories": 999}}
        result = ai_cache_service.get_cached_response(
            db, context_hash=ai_cache_service.context_hash(other)
        )
        assert result is None

    def test_cache_hit(self, db):
        ai_cache_service.save_response(
            db,
            meal_id=1,
            provider="gemini",
            model="gemini-2.0-flash",
            context=SAMPLE_CONTEXT,
            response=SAMPLE_RESPONSE,
        )
        result = ai_cache_service.get_cached_response(
            db,
            context_hash=ai_cache_service.context_hash(SAMPLE_CONTEXT),
            provider="gemini",
        )
        assert result is not None
        assert result.meal_id == 1
        assert result.summary == "A balanced vegetarian meal."
        assert result.health_score == 72
        assert result.recommendations_json == ["Add fiber"]
        assert result.alternatives_json == ["Brown rice instead of white"]
        assert result.warnings_json == ["Sodium is moderate"]
        assert result.follow_up_questions_json == ["Would you like dinner ideas?"]


class TestInvalidation:
    def test_invalidate_by_meal_id(self, db):
        ai_cache_service.save_response(
            db, meal_id=1, provider="gemini", model="m", context=SAMPLE_CONTEXT,
            response=SAMPLE_RESPONSE,
        )
        deleted = ai_cache_service.invalidate(db, meal_id=1)
        assert deleted == 1
        result = ai_cache_service.get_cached_response(
            db, context_hash=ai_cache_service.context_hash(SAMPLE_CONTEXT)
        )
        assert result is None

    def test_invalidate_by_context_hash(self, db):
        ai_cache_service.save_response(
            db, meal_id=1, provider="gemini", model="m", context=SAMPLE_CONTEXT,
            response=SAMPLE_RESPONSE,
        )
        deleted = ai_cache_service.invalidate(
            db, context_hash=ai_cache_service.context_hash(SAMPLE_CONTEXT)
        )
        assert deleted == 1
        assert db.query(AIDietitianResult).count() == 0

    def test_invalidate_only_matching_rows(self, db):
        ai_cache_service.save_response(
            db, meal_id=1, provider="gemini", model="m", context=SAMPLE_CONTEXT,
            response=SAMPLE_RESPONSE,
        )
        other = {**SAMPLE_CONTEXT, "nutrition": {"calories": 999}}
        ai_cache_service.save_response(
            db, meal_id=2, provider="gemini", model="m", context=other,
            response=SAMPLE_RESPONSE,
        )
        # Invalidate only meal_id=1
        ai_cache_service.invalidate(db, meal_id=1)
        assert db.query(AIDietitianResult).count() == 1


class TestProviderIsolation:
    def test_provider_isolation(self, db):
        ai_cache_service.save_response(
            db, meal_id=1, provider="gemini", model="gemini-2.0-flash",
            context=SAMPLE_CONTEXT, response=SAMPLE_RESPONSE,
        )
        # Same context, different provider -> separate cache entry
        ai_cache_service.save_response(
            db, meal_id=1, provider="claude", model="claude-3",
            context=SAMPLE_CONTEXT, response={**SAMPLE_RESPONSE, "summary": "Claude view"},
        )
        gemini = ai_cache_service.get_cached_response(
            db, context_hash=ai_cache_service.context_hash(SAMPLE_CONTEXT),
            provider="gemini",
        )
        claude = ai_cache_service.get_cached_response(
            db, context_hash=ai_cache_service.context_hash(SAMPLE_CONTEXT),
            provider="claude",
        )
        assert gemini is not None and gemini.provider == "gemini"
        assert claude is not None and claude.provider == "claude"
        assert gemini.summary == "A balanced vegetarian meal."
        assert claude.summary == "Claude view"


class TestPromptVersion:
    def test_prompt_version_change_serves_miss(self, db):
        ai_cache_service.save_response(
            db, meal_id=1, provider="gemini", model="m", context=SAMPLE_CONTEXT,
            response=SAMPLE_RESPONSE, prompt_version="1",
        )
        result = ai_cache_service.get_cached_response(
            db,
            context_hash=ai_cache_service.context_hash(SAMPLE_CONTEXT),
            prompt_version="2",  # prompt was changed -> logical miss
        )
        assert result is None
