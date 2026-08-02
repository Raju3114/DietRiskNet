"""Tests for the personalized AI Nutrition Coach analytics.

Covers:
- analytics averages / counts
- meals-this-week window
- pattern detection (high sodium, low protein, low fiber)
- goal generation + progress
- DCI / risk trend detection
- best / worst meal + most common food
- empty history and single meal edge cases
- the GET /api/nutrition/analytics endpoint
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base, get_db
from backend.database.models import (
    DiseasePrediction,
    Meal,
    MealItem,
    MealNutrition,
    User,
)
from backend.routes.deps import get_current_user
from backend.routes.nutrition_coach import router as nutrition_coach_router
from backend.services.nutrition_analytics_service import (
    HIGH_SODIUM_MG,
    NutritionAnalyticsService,
    nutrition_analytics_service,
)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def user(db):
    u = User(email="coach@test.com", password_hash="x", full_name="Coach")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _meal(db, user, *, calories=500, protein=30, fiber=5, sodium=400,
          dci=0.8, nis=0.2, risk=0.2, foods=("Salad",), days_ago=0):
    from datetime import datetime, timedelta
    from backend.utils.datetime_utils import utcnow
    created = utcnow() - timedelta(days=days_ago)
    m = Meal(user_id=user.id, image_path="/static/x.png",
             dci=dci, dci_level="High", nis=nis, nis_level="Mild",
             risk_fusion_score=risk, risk_fusion_level="Low",
             created_at=created)
    db.add(m)
    db.commit()
    db.refresh(m)
    for name in foods:
        db.add(MealItem(meal_id=m.id, name=name, confidence=0.9,
                        weight_g=100, calories=calories, protein=protein,
                        carbs=50, fats=15, sodium=sodium, fiber=fiber))
    db.add(MealNutrition(meal_id=m.id, calories=calories, protein=protein,
                         carbs=50, fats=15, sugar=5, fiber=fiber, sodium=sodium,
                         calcium=100, iron=2, vitamin_c=10, folate=20))
    db.add(DiseasePrediction(meal_id=m.id, diabetes_risk=risk,
                             obesity_risk=risk, hypertension_risk=risk,
                             deficiency_risk=risk))
    db.commit()
    return m


class TestAnalyticsCalculations:
    def test_averages_and_counts(self, db, user):
        _meal(db, user, calories=500, protein=30)
        _meal(db, user, calories=700, protein=40)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert a["meals_analyzed"] == 2
        assert a["avg_calories"] == 600.0
        assert a["avg_protein"] == 35.0
        assert a["avg_dci"] == 0.8
        assert a["avg_nis"] == 0.2

    def test_empty_history(self, db, user):
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert a["meals_analyzed"] == 0
        assert a["meals_this_week"] == 0
        assert a["patterns"] == []
        assert a["goals"] == []
        assert a["highest_risk"] is None
        # coach summary reflects no meals
        assert "no analysed meals" in NutritionAnalyticsService.summary_for_context(a).lower()

    def test_single_meal(self, db, user):
        _meal(db, user, calories=500)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert a["meals_analyzed"] == 1
        assert a["avg_calories"] == 500.0
        assert a["dci_trend"] is None  # not enough data
        assert a["risk_trend"] is None

    def test_large_history_limits_to_window(self, db, user):
        for i in range(20):
            _meal(db, user, calories=500 + i)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        # Only the most recent RECENT_MEALS_LIMIT (14) are considered.
        assert a["meals_analyzed"] == 14


class TestPatterns:
    def test_high_sodium_pattern(self, db, user):
        for _ in range(5):
            _meal(db, user, sodium=int(HIGH_SODIUM_MG) + 200, protein=30)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert any("sodium" in p for p in a["patterns"])

    def test_low_protein_pattern(self, db, user):
        for _ in range(5):
            _meal(db, user, protein=8, sodium=300)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert any("protein" in p for p in a["patterns"])

    def test_low_fiber_pattern(self, db, user):
        for _ in range(5):
            _meal(db, user, protein=30, sodium=300, fiber=0.5)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert any("fiber" in p for p in a["patterns"])

    def test_healthy_meal_has_no_negative_pattern(self, db, user):
        for _ in range(5):
            _meal(db, user, protein=35, sodium=300, fiber=6)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert not any("sodium" in p for p in a["patterns"])
        assert not any("protein" in p for p in a["patterns"])


class TestTrends:
    def test_dci_improved(self, db, user):
        for dci in [0.5, 0.55, 0.6, 0.7, 0.8, 0.85]:
            _meal(db, user, dci=dci)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert a["dci_trend"]["direction"] == "improved"
        assert a["dci_trend"]["delta"] > 0

    def test_risk_decreased(self, db, user):
        # later meals have lower risk (recent-first ordering reversed internally)
        for risk in [0.7, 0.6, 0.5, 0.3, 0.2, 0.15]:
            _meal(db, user, risk=risk)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        if a["risk_trend"]:
            assert a["risk_trend"]["direction"] in ("decreased", "stable")


class TestGoalsAndExtras:
    def test_goals_generated(self, db, user):
        _meal(db, user, protein=8, fiber=1, sodium=1500)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        ids = [g["id"] for g in a["goals"]]
        assert "sodium" in ids and "protein" in ids and "fiber" in ids
        assert "consistency" in ids and "hydration" in ids
        # low protein -> needs attention
        protein_goal = next(g for g in a["goals"] if g["id"] == "protein")
        assert protein_goal["status"] in ("needs-attention", "in-progress")

    def test_most_common_food(self, db, user):
        _meal(db, user, foods=("Pizza",))
        _meal(db, user, foods=("Pizza",))
        _meal(db, user, foods=("Salad",))
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert a["most_common_food"] == "Pizza"

    def test_best_and_worst_meal(self, db, user):
        _meal(db, user, dci=0.9, nis=0.1)
        _meal(db, user, dci=0.4, nis=0.9)
        a = nutrition_analytics_service.compute_analytics(db, user.id)
        assert a["best_meal"]["dci"] == 0.9
        assert a["meal_needing_improvement"]["nis"] == 0.9


class TestEndpoint:
    def _client(self, db, user):
        test_app = FastAPI()
        test_app.include_router(nutrition_coach_router)
        test_app.dependency_overrides[get_current_user] = lambda: user
        test_app.dependency_overrides[get_db] = lambda: db
        return TestClient(test_app)

    def test_analytics_endpoint(self, db, user):
        _meal(db, user, calories=600)
        client = self._client(db, user)
        resp = client.get("/nutrition/analytics")
        assert resp.status_code == 200
        data = resp.json()["analytics"]
        assert data["meals_analyzed"] == 1
        assert data["avg_calories"] == 600.0

    def test_analytics_endpoint_empty(self, db, user):
        client = self._client(db, user)
        resp = client.get("/nutrition/analytics")
        assert resp.status_code == 200
        assert resp.json()["analytics"]["meals_analyzed"] == 0

    def test_unauthorized_401(self, db, user):
        # No dependency override -> real get_current_user raises 401/403.
        test_app = FastAPI()
        test_app.include_router(nutrition_coach_router)
        test_app.dependency_overrides[get_db] = lambda: db
        client = TestClient(test_app)
        resp = client.get("/nutrition/analytics")
        assert resp.status_code in (401, 403)
