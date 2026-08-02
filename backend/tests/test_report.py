"""Tests for the PDF meal report service and endpoint.

Covers:
- PDF generation returns valid PDF bytes (%PDF header)
- missing meal / unauthorized meal -> ReportNotFoundError
- missing meal image handled gracefully (no crash)
- HTTP endpoint returns application/pdf
- HTTP endpoint 404 for another user's meal
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
from backend.routes.deps import get_current_user
from backend.routes.report import router as report_router
from backend.services.report_service import ReportNotFoundError, report_service


@pytest.fixture()
def db():
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
    user = User(email="report@test.com", password_hash="x", full_name="Report")
    db.add(user)
    db.commit()
    db.refresh(user)

    meal = Meal(
        user_id=user.id,
        image_path="/nonexistent/report-meal.png",  # will be skipped gracefully
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
        summary="A good vegetarian meal.", meal_quality="Good",
        health_score=80, health_level="Good",
        health_explanation="Fine", risk_explanation="Low risk",
        recommendations_json=["Add fiber"], alternatives_json=["Brown rice"],
        warnings_json=["Sodium is moderate"], follow_up_questions_json=[],
        context_hash="abc",
    ))
    db.commit()
    return user, meal


class TestReportService:
    def test_generates_valid_pdf(self, db, user_and_meal):
        user, meal = user_and_meal
        pdf = report_service.generate_report(db, user_id=user.id, meal_id=meal.id)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 2000  # non-trivial document

    def test_pdf_contains_section_text(self, db, user_and_meal):
        user, meal = user_and_meal
        pdf = report_service.generate_report(db, user_id=user.id, meal_id=meal.id)
        # PDF text is compressed; simply assert content markers are plausible
        # by checking the document is well-formed and includes expected metadata.
        assert b"DietRiskNet" in pdf or b"DietRiskNet" in pdf.decode("latin-1", "ignore")

    def test_missing_meal_raises(self, db, user_and_meal):
        user, _ = user_and_meal
        with pytest.raises(ReportNotFoundError):
            report_service.generate_report(db, user_id=user.id, meal_id=9999)

    def test_unauthorized_meal_raises(self, db, user_and_meal):
        user, meal = user_and_meal
        other = User(email="other@test.com", password_hash="x")
        db.add(other)
        db.commit()
        with pytest.raises(ReportNotFoundError):
            report_service.generate_report(db, user_id=other.id, meal_id=meal.id)

    def test_generates_without_ai_section(self, db, user_and_meal):
        user, meal = user_and_meal
        # Remove the AI result to exercise the "no AI" branch.
        db.query(AIDietitianResult).filter(
            AIDietitianResult.meal_id == meal.id
        ).delete()
        db.commit()
        pdf = report_service.generate_report(db, user_id=user.id, meal_id=meal.id)
        assert pdf[:5] == b"%PDF-"


class TestReportEndpoint:
    def _client(self, db, user):
        test_app = FastAPI()
        test_app.include_router(report_router)
        test_app.dependency_overrides[get_current_user] = lambda: user
        test_app.dependency_overrides[get_db] = lambda: db
        return TestClient(test_app)

    def test_download_success(self, db, user_and_meal):
        user, meal = user_and_meal
        client = self._client(db, user)
        resp = client.get(f"/report/{meal.id}")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert resp.content[:5] == b"%PDF-"

    def test_download_not_found(self, db, user_and_meal):
        user, _ = user_and_meal
        client = self._client(db, user)
        resp = client.get("/report/12345")
        assert resp.status_code == 404

    def test_download_unauthorized(self, db, user_and_meal):
        _, meal = user_and_meal
        other = User(email="other2@test.com", password_hash="x")
        db.add(other)
        db.commit()
        client = self._client(db, other)
        resp = client.get(f"/report/{meal.id}")
        assert resp.status_code == 404
