"""DCI longitudinal semantics tests.

DCI represents *longitudinal* dietary consistency and therefore requires
>= 2 DISTINCT calendar days with valid (non-zero) nutrition data within the
last 7 days.  With fewer valid days — or a zero-calorie history — DCI is
unavailable (None, "Insufficient Data") and must NOT fall back to a single
meal's macro balance or a fabricated perfect score.
"""

import pytest
from datetime import timedelta

from backend.database.database import SessionLocal
from backend.database.models import User, Meal, MealNutrition
from backend.services.indices_services import dci_service
from backend.utils.datetime_utils import utcnow


@pytest.fixture(scope="module")
def db():
    session = SessionLocal()
    yield session
    session.close()


def _add_meal(db, user_id, days_ago, kcal):
    m = Meal(user_id=user_id, created_at=utcnow() - timedelta(days=days_ago))
    db.add(m)
    db.flush()
    db.add(MealNutrition(meal_id=m.id, calories=kcal, protein=10, carbs=50, fats=10))
    db.commit()


def _dci(db, meals):
    user = User(email=f"dci-test-{id(meals)}@example.com", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    for days_ago, kcal in meals:
        _add_meal(db, user.id, days_ago, kcal)
    score, level = dci_service.calculate({}, user.id, db)
    db.delete(user)  # cascade removes meals/nutrition
    db.commit()
    return score, level


def test_zero_days_unavailable(db):
    score, level = _dci(db, [])
    assert score is None
    assert level == "Insufficient Data"


def test_one_valid_day_unavailable(db):
    score, level = _dci(db, [(0, 650)])
    assert score is None
    assert level == "Insufficient Data"


def test_multiple_meals_same_day_unavailable(db):
    score, level = _dci(db, [(0, 650), (0, 700), (0, 800)])
    assert score is None
    assert level == "Insufficient Data"


def test_two_identical_days_high(db):
    score, level = _dci(db, [(0, 2000), (1, 2000)])
    assert score is not None and score > 0.9
    assert level == "High Consistency"


def test_two_varying_days_lower(db):
    score, level = _dci(db, [(0, 1800), (1, 2600)])
    assert score is not None and score < 0.9
    assert score is not None and score > 0.5


def test_three_consistent_days_high(db):
    score, level = _dci(db, [(0, 2000), (1, 2050), (2, 2100)])
    assert score is not None and score > 0.9
    assert level == "High Consistency"


def test_zero_calorie_history_unavailable(db):
    # Zero-calorie days must not establish history and must not yield DCI=1.0.
    score, level = _dci(db, [(0, 0), (1, 0)])
    assert score is None
    assert level == "Insufficient Data"


def test_mixed_zero_and_valid_days_counts_only_valid(db):
    # A zero-calorie day is excluded; 2 valid days -> longitudinal DCI.
    score, level = _dci(db, [(0, 0), (1, 2000), (2, 2100)])
    assert score is not None
    assert score > 0.9
