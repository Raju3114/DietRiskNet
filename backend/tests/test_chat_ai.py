"""Tests for the meal-specific AI Dietitian chat.

Covers:
- context loading from the persisted meal (no recomputation)
- chat reply generation
- rolling session history (max 10 messages)
- meal-not-found / unauthorized handling
- provider disabled / timeout failure modes
- HTTP endpoint: success, friendly failure, empty message, 404
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base, get_db
from backend.database.models import (
    AIDietitianResult,
    DiseasePrediction,
    Meal,
    MealItem,
    MealNutrition,
    Recommendation,
    RiskFusionResult,
    User,
)
from backend.exceptions.gemini_exceptions import LLMProviderError
from backend.routes.ai_chat import router as ai_chat_router
from backend.routes.deps import get_current_user
from backend.services.chat_ai_service import (
    ChatAIService,
    MealNotFoundError,
)
from backend.services.llm.base import LLMClient


class FakeLLMClient(LLMClient):
    def __init__(self, *, enabled=True, reply="A helpful answer.", error=None):
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
    # StaticPool + check_same_thread=False lets the in-memory SQLite
    # connection be shared across the TestClient's worker thread.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
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
def user_and_meal(db):
    user = User(email="chat@test.com", password_hash="x", full_name="Chat")
    db.add(user)
    db.commit()
    db.refresh(user)

    meal = Meal(
        user_id=user.id,
        image_path="/static/x.png",
        dci=0.8,
        dci_level="High Consistency",
        nis=0.3,
        nis_level="Mild Imbalance",
        risk_fusion_score=0.25,
        risk_fusion_level="Low",
        notes="",
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    db.add(MealItem(
        meal_id=meal.id, name="Vegetable samosa", confidence=0.9,
        weight_g=100, calories=97, protein=2.0, carbs=10.0, fats=5.0,
    ))
    db.add(MealNutrition(
        meal_id=meal.id, calories=97, protein=2, carbs=10, fats=5,
        sugar=3, fiber=1, sodium=300, calcium=10, iron=1,
        vitamin_c=2, folate=5,
    ))
    db.add(DiseasePrediction(
        meal_id=meal.id, diabetes_risk=0.2, obesity_risk=0.3,
        hypertension_risk=0.1, deficiency_risk=0.2,
    ))
    db.add(RiskFusionResult(meal_id=meal.id, fused_score=0.25, risk_level="Low"))
    db.add(Recommendation(
        meal_id=meal.id, content="Eat well", explanation="Balanced",
        category="General",
    ))
    db.add(AIDietitianResult(
        meal_id=meal.id, provider="gemini", model="m",
        summary="Good meal", health_score=80, health_level="Good",
        health_explanation="Fine", risk_explanation="Low risk",
        recommendations_json=["Add fiber"], alternatives_json=["Brown rice"],
        warnings_json=[], follow_up_questions_json=[],
        context_hash="abc",
    ))
    db.commit()
    return user, meal


class TestContextLoading:
    def test_loads_meal_without_recompute(self, db, user_and_meal):
        user, meal = user_and_meal
        client = FakeLLMClient()
        service = ChatAIService(client=client)
        context = service.build_context_from_meal(db, user.id, meal.id)

        assert context["foods"][0]["name"] == "Vegetable samosa"
        assert context["nutrition"]["calories"] == 97
        assert context["dci"] == {"score": 0.8, "level": "High Consistency"}
        assert context["nis"]["score"] == 0.3
        assert context["risk_prediction"]["diabetes_risk"] == 0.2
        assert context["fusion"]["fused_score"] == 0.25
        assert context["rule_based_recommendations"][0]["category"] == "General"
        assert context["ai_summary"] == "Good meal"
        assert context["health_score"] == 80
        assert client.calls == 0  # no LLM involved in context loading


class TestChat:
    def test_returns_reply_and_stores_history(self, db, user_and_meal):
        user, meal = user_and_meal
        client = FakeLLMClient(reply="Reduce salt.")
        service = ChatAIService(client=client)
        reply = service.chat(db, user_id=user.id, meal_id=meal.id, message="How can I reduce sodium?")
        assert reply == "Reduce salt."
        assert client.calls == 1
        session = service._sessions[(user.id, meal.id)]
        assert len(session.history) == 2
        assert session.history[0] == {"role": "user", "content": "How can I reduce sodium?"}
        assert session.history[1] == {"role": "model", "content": "Reduce salt."}

    def test_history_rolling_max_10(self, db, user_and_meal):
        user, meal = user_and_meal
        client = FakeLLMClient(reply="ok")
        service = ChatAIService(client=client)
        for i in range(6):  # 6 exchanges = 12 entries, capped to 10
            service.chat(db, user_id=user.id, meal_id=meal.id, message=f"q{i}")
        session = service._sessions[(user.id, meal.id)]
        assert len(session.history) == 10  # MAX_HISTORY_MESSAGES
        # The two oldest entries (q0 + its reply) were dropped.
        assert session.history[0] == {"role": "user", "content": "q1"}
        assert session.history[-1] == {"role": "model", "content": "ok"}
        assert "q0" not in [m["content"] for m in session.history]

    def test_same_session_reused_for_same_meal(self, db, user_and_meal):
        user, meal = user_and_meal
        client = FakeLLMClient(reply="ok")
        service = ChatAIService(client=client)
        service.chat(db, user_id=user.id, meal_id=meal.id, message="q1")
        service.chat(db, user_id=user.id, meal_id=meal.id, message="q2")
        session = service._sessions[(user.id, meal.id)]
        assert len(session.history) == 4  # two exchanges remembered


class TestChatErrors:
    def test_meal_not_found(self, db, user_and_meal):
        user, _ = user_and_meal
        client = FakeLLMClient()
        service = ChatAIService(client=client)
        with pytest.raises(MealNotFoundError):
            service.chat(db, user_id=user.id, meal_id=9999, message="hi")

    def test_unauthorized_meal(self, db, user_and_meal):
        user, meal = user_and_meal
        other = User(email="other@test.com", password_hash="x")
        db.add(other)
        db.commit()
        client = FakeLLMClient()
        service = ChatAIService(client=client)
        with pytest.raises(MealNotFoundError):
            service.chat(db, user_id=other.id, meal_id=meal.id, message="hi")

    def test_provider_disabled_raises(self, db, user_and_meal):
        user, meal = user_and_meal
        client = FakeLLMClient(enabled=False)
        service = ChatAIService(client=client)
        with pytest.raises(LLMProviderError):
            service.chat(db, user_id=user.id, meal_id=meal.id, message="hi")

    def test_provider_timeout_propagates(self, db, user_and_meal):
        user, meal = user_and_meal
        client = FakeLLMClient(
            error=LLMProviderError("timed out")
        )
        service = ChatAIService(client=client)
        with pytest.raises(LLMProviderError):
            service.chat(db, user_id=user.id, meal_id=meal.id, message="hi")


# ----------------------------------------------------------------------
# HTTP endpoint tests
# ----------------------------------------------------------------------

def make_test_client(db, user):
    test_app = FastAPI()
    test_app.include_router(ai_chat_router)
    test_app.dependency_overrides[get_current_user] = lambda: user
    test_app.dependency_overrides[get_db] = lambda: db
    return TestClient(test_app)


class TestChatEndpoint:
    def test_success(self, db, user_and_meal, monkeypatch):
        user, meal = user_and_meal
        client = make_test_client(db, user)

        def fake_chat(_db, *, user_id, meal_id, message):
            return "Here is some advice."

        monkeypatch.setattr(
            "backend.routes.ai_chat.chat_ai_service.chat", fake_chat
        )
        resp = client.post(
            "/ai/chat",
            json={"meal_id": meal.id, "message": "How can I reduce sodium?"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"reply": "Here is some advice."}

    def test_unavailable_returns_friendly_reply(self, db, user_and_meal, monkeypatch):
        user, meal = user_and_meal
        client = make_test_client(db, user)

        def fake_chat(_db, *, user_id, meal_id, message):
            raise LLMProviderError("no key")

        monkeypatch.setattr(
            "backend.routes.ai_chat.chat_ai_service.chat", fake_chat
        )
        resp = client.post(
            "/ai/chat",
            json={"meal_id": meal.id, "message": "hello"},
        )
        assert resp.status_code == 200  # never 500
        assert "unavailable" in resp.json()["reply"].lower()

    def test_empty_message_400(self, db, user_and_meal):
        user, meal = user_and_meal
        client = make_test_client(db, user)
        resp = client.post("/ai/chat", json={"meal_id": meal.id, "message": "   "})
        assert resp.status_code == 400

    def test_missing_message_422(self, db, user_and_meal):
        user, meal = user_and_meal
        client = make_test_client(db, user)
        resp = client.post("/ai/chat", json={"meal_id": meal.id})
        assert resp.status_code == 422  # pydantic validation

    def test_meal_not_found_404(self, db, user_and_meal, monkeypatch):
        user, _ = user_and_meal
        client = make_test_client(db, user)

        def fake_chat(_db, *, user_id, meal_id, message):
            raise MealNotFoundError("not found")

        monkeypatch.setattr(
            "backend.routes.ai_chat.chat_ai_service.chat", fake_chat
        )
        resp = client.post("/ai/chat", json={"meal_id": 12345, "message": "hi"})
        assert resp.status_code == 404
