"""Tests for the AI Nutrition Assistant.

Covers:
- out-of-scope questions return the polite canned reply (no LLM call)
- reply generation + rolling history
- meal-history context built from stored data (no ML re-run)
- provider disabled / failure -> LLMProviderError
- HTTP endpoint: success, empty message, missing message, friendly failure
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
    RiskFusionResult,
    User,
    UserSetting,
)
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.routes.deps import get_current_user
from backend.routes.nutrition_chat import router as nutrition_chat_router
from backend.services.llm.base import LLMClient
from backend.services.nutrition_assistant_service import (
    OUT_OF_SCOPE_REPLY,
    NutritionAssistantService,
)


class FakeLLMClient(LLMClient):
    def __init__(self, *, enabled=True, reply="Eat more fiber.", error=None):
        self._enabled = enabled
        self._reply = reply
        self._error = error
        self.calls = 0

    @property
    def enabled(self):
        return self._enabled

    def generate_json(self, system_prompt, user_prompt):
        self.calls += 1
        if self._error:
            raise self._error
        return {"reply": self._reply}


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
    u = User(email="nutri@test.com", password_hash="x", full_name="Nutri")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _seed_meal(db, user, *, foods=("Vegetable samosa",), calories=500, sodium=1500):
    meal = Meal(
        user_id=user.id, image_path="/static/x.png",
        dci=0.6, dci_level="Low Consistency", nis=0.5, nis_level="Moderate Imbalance",
        risk_fusion_score=0.5, risk_fusion_level="Moderate",
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)
    for name in foods:
        db.add(MealItem(meal_id=meal.id, name=name, confidence=0.9,
                        weight_g=100, calories=calories // len(foods), protein=5,
                        carbs=20, fats=5, sodium=sodium))
    db.add(MealNutrition(meal_id=meal.id, calories=calories, protein=10, carbs=60,
                         fats=15, sugar=8, fiber=3, sodium=sodium, calcium=100,
                         iron=2, vitamin_c=10, folate=20))
    db.add(DiseasePrediction(meal_id=meal.id, diabetes_risk=0.3, obesity_risk=0.4,
                             hypertension_risk=0.6, deficiency_risk=0.2))
    db.add(RiskFusionResult(meal_id=meal.id, fused_score=0.5, risk_level="Moderate"))
    db.commit()
    return meal


class TestService:
    def test_off_topic_returns_canned_reply_no_llm_call(self, db, user):
        client = FakeLLMClient()
        service = NutritionAssistantService(client=client)
        reply = service.chat(db, user_id=user.id, message="What do you think about politics?")
        assert reply == OUT_OF_SCOPE_REPLY
        assert client.calls == 0  # no LLM call for obvious off-topic

    def test_normal_question_returns_reply_and_stores_history(self, db, user):
        client = FakeLLMClient(reply="Start with oatmeal and fruit.")
        service = NutritionAssistantService(client=client)
        reply = service.chat(db, user_id=user.id, message="Suggest a healthy breakfast")
        assert reply == "Start with oatmeal and fruit."
        assert client.calls == 1
        session = service._store.get(user.id)
        assert len(session.history) == 2
        assert session.history[0] == {"role": "user", "content": "Suggest a healthy breakfast"}

    def test_rolling_history(self, db, user):
        client = FakeLLMClient(reply="ok")
        service = NutritionAssistantService(client=client)
        for i in range(6):
            service.chat(db, user_id=user.id, message=f"q{i}")
        session = service._store.get(user.id)
        assert len(session.history) == 10  # max window

    def test_context_includes_recent_meals(self, db, user):
        _seed_meal(db, user, foods=("Vegetable samosa",), sodium=1500)
        context = NutritionAssistantService.build_user_context(db, user.id)
        assert len(context["recent_meals"]) == 1
        meal = context["recent_meals"][0]
        assert meal["foods"] == ["Vegetable samosa"]
        assert meal["calories"] == 500
        assert meal["hypertension_risk"] == 0.6
        assert meal["dci"] == 0.6
        assert meal["nis"] == 0.5

    def test_context_empty_when_no_meals(self, db, user):
        context = NutritionAssistantService.build_user_context(db, user.id)
        assert context["recent_meals"] == []

    def test_provider_disabled_raises(self, db, user):
        client = FakeLLMClient(enabled=False)
        service = NutritionAssistantService(client=client)
        with pytest.raises(LLMProviderError):
            service.chat(db, user_id=user.id, message="Suggest a snack")

    def test_provider_failure_raises(self, db, user):
        client = FakeLLMClient(error=LLMProviderError("timed out"))
        service = NutritionAssistantService(client=client)
        with pytest.raises(LLMProviderError):
            service.chat(db, user_id=user.id, message="Suggest a snack")


class TestEndpoint:
    def _client(self, db, user):
        test_app = FastAPI()
        test_app.include_router(nutrition_chat_router)
        test_app.dependency_overrides[get_current_user] = lambda: user
        test_app.dependency_overrides[get_db] = lambda: db
        return TestClient(test_app)

    def test_success(self, db, user, monkeypatch):
        client = self._client(db, user)

        def fake_chat(_db, *, user_id, message, include_history):
            return "A balanced diet includes a variety of foods."

        monkeypatch.setattr(
            "backend.routes.nutrition_chat.nutrition_assistant_service.chat",
            fake_chat,
        )
        resp = client.post("/nutrition-chat", json={"message": "What is a balanced diet?"})
        assert resp.status_code == 200
        assert resp.json() == {"reply": "A balanced diet includes a variety of foods."}

    def test_unavailable_returns_friendly_reply(self, db, user, monkeypatch):
        client = self._client(db, user)

        def fake_chat(_db, *, user_id, message, include_history):
            raise LLMProviderError("no key")

        monkeypatch.setattr(
            "backend.routes.nutrition_chat.nutrition_assistant_service.chat",
            fake_chat,
        )
        resp = client.post("/nutrition-chat", json={"message": "hello"})
        assert resp.status_code == 200  # never 500
        assert "unavailable" in resp.json()["reply"].lower()

    def test_empty_message_400(self, db, user):
        client = self._client(db, user)
        resp = client.post("/nutrition-chat", json={"message": "   "})
        assert resp.status_code == 400

    def test_missing_message_422(self, db, user):
        client = self._client(db, user)
        resp = client.post("/nutrition-chat", json={})
        assert resp.status_code == 422
