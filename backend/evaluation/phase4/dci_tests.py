"""Phase 4 — Part 11: DCI final controlled evaluation.

Verifies DCI longitudinal semantics against a TEMPORARY SQLite database:

    < 2 distinct valid days  -> unavailable (None, "Insufficient Data")
    >= 2 distinct valid days -> longitudinal DCI (calorie consistency)

DCI measures day-to-day consistency of daily calorie totals, not diet quality.
All records are created and removed inside the temporary database.
"""

import os
import sys
import tempfile

# Point the app at a throwaway database BEFORE any backend import.
_TMP_DB = os.path.join(tempfile.gettempdir(), "phase4_dci_tmp.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"

from datetime import timedelta  # noqa: E402

from backend.database.database import Base, engine, SessionLocal  # noqa: E402
import backend.database.models  # noqa: E402, F401
from backend.services.indices_services import dci_service  # noqa: E402
from backend.utils.datetime_utils import utcnow  # noqa: E402
from backend.evaluation.phase4.helpers import write_csv, write_json  # noqa: E402


def _add_meal(db, user_id, days_ago, kcal):
    from backend.database.models import Meal, MealNutrition
    m = Meal(user_id=user_id, created_at=utcnow() - timedelta(days=days_ago))
    db.add(m)
    db.flush()
    db.add(MealNutrition(meal_id=m.id, calories=kcal, protein=10, carbs=50, fats=10))
    db.commit()


def _run(meals: list) -> tuple:
    """meals: list of (days_ago, kcal). Returns (valid_days, daily_calories, score, level)."""
    db = SessionLocal()
    from backend.database.models import User
    u = User(email=f"dci-eval-{abs(hash(tuple(meals)))}@example.com", password_hash="x")
    db.add(u)
    db.commit()
    db.refresh(u)
    for days_ago, kcal in meals:
        _add_meal(db, u.id, days_ago, kcal)
    score, level = dci_service.calculate({}, u.id, db)
    # recompute valid days & daily totals for the report
    from backend.database.models import Meal
    past = db.query(Meal).filter(Meal.user_id == u.id).all()
    daily = {}
    for m in past:
        cal = m.nutrition.calories if m.nutrition else 0.0
        if cal > 0:
            day = m.created_at.strftime("%Y-%m-%d")
            daily[day] = daily.get(day, 0.0) + cal
    db.delete(u)
    db.commit()
    db.close()
    return len(daily), daily, score, level


SCENARIOS = [
    ("0_valid_days", []),
    ("1_valid_day", [(0, 2000)]),
    ("multiple_meals_same_day", [(0, 650), (0, 700), (0, 800)]),
    ("2_consistent_days", [(0, 2000), (1, 2000)]),
    ("2_varying_days", [(0, 1800), (1, 2600)]),
    ("3_consistent_days", [(0, 2000), (1, 2050), (2, 2100)]),
    ("3_highly_varying_days", [(0, 1200), (1, 2600), (2, 3200)]),
    ("7_consistent_days", [(d, 2000) for d in range(7)]),
    ("7_varying_days", [(d, 1400 + d * 250) for d in range(7)]),
    ("zero_calorie_history", [(0, 0), (1, 0)]),
]


def main() -> dict:
    Base.metadata.create_all(bind=engine)
    rows = []
    for name, meals in SCENARIOS:
        valid_days, daily, score, level = _run(meals)
        rows.append({
            "scenario": name,
            "distinct_valid_days": valid_days,
            "daily_calories": json_serialize(daily),
            "dci": "None" if score is None else round(score, 4),
            "dci_level": level,
        })
        score_s = "None" if score is None else f"{score:.4f}"
        print(f"{name:>24}: valid_days={valid_days}  DCI={score_s} ({level})")

    write_csv("dci_controlled_tests.csv", rows)
    summary = {
        "scenarios": rows,
        "requirement": ">=2 distinct valid days within last 7 days",
        "dci_measures": "consistency of daily total calorie intake (CV), not diet quality",
    }
    write_json("dci_evaluation.json", summary)
    return summary


def json_serialize(d: dict) -> str:
    return ";".join(f"{k}={v:g}" for k, v in sorted(d.items()))


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            from backend.database.database import engine as _eng
            _eng.dispose()
        except Exception:
            pass
        if os.path.exists(_TMP_DB):
            try:
                os.remove(_TMP_DB)
            except PermissionError:
                pass
