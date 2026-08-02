"""Benchmark PDF report generation.

Measures:
- ``pdf_generation`` latency (mean / median / p95)
- average PDF size in bytes
"""

from __future__ import annotations

import argparse
import os
from typing import Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base
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
from backend.evaluation.system_metrics import (
    DEFAULT_OUTPUT_DIR,
    StatsCollector,
    timer,
    write_csv,
    write_json,
)


def _seed_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    user = User(email="pdf@test.com", password_hash="x", full_name="PDF")
    session.add(user)
    session.commit()
    session.refresh(user)

    meal = Meal(
        user_id=user.id, image_path="/nonexistent/meal.png",
        dci=0.8, dci_level="High Consistency", nis=0.3,
        nis_level="Mild Imbalance", risk_fusion_score=0.25,
        risk_fusion_level="Low",
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)

    session.add(MealItem(
        meal_id=meal.id, name="Vegetable samosa", confidence=0.9,
        weight_g=100, calories=97, protein=2, carbs=10, fats=5,
    ))
    session.add(MealNutrition(
        meal_id=meal.id, calories=97, protein=2, carbs=10, fats=5,
        sugar=3, fiber=1, sodium=300, calcium=10, iron=1,
        vitamin_c=2, folate=5,
    ))
    session.add(DiseasePrediction(
        meal_id=meal.id, diabetes_risk=0.2, obesity_risk=0.3,
        hypertension_risk=0.1, deficiency_risk=0.2,
    ))
    session.add(RiskFusionResult(meal_id=meal.id, fused_score=0.25, risk_level="Low"))
    session.add(Recommendation(
        meal_id=meal.id, content="Eat well", explanation="Balanced",
        category="General",
    ))
    session.add(AIDietitianResult(
        meal_id=meal.id, provider="gemini", model="m",
        summary="A balanced meal.", meal_quality="Good",
        health_score=80, health_level="Good", health_explanation="Fine",
        risk_explanation="Low risk.", recommendations_json=["Add fiber"],
        alternatives_json=["Brown rice"], warnings_json=[],
        follow_up_questions_json=[], context_hash="abc",
    ))
    session.commit()
    # Fresh in-memory DB: the seeded user and meal both have id == 1.
    return session


def run_benchmark(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    iterations: int = 5,
    db: Optional[object] = None,
    user_id: Optional[int] = None,
    meal_id: Optional[int] = None,
) -> Dict[str, object]:
    """Run the PDF generation benchmark.

    ``db`` / ``user_id`` / ``meal_id`` may be injected for tests.  When
    ``db`` is None a fresh seeded in-memory database is created.
    """
    from backend.services.report_service import report_service

    own_db = db is None
    session = db or _seed_db()
    uid = user_id if user_id is not None else 1
    mid = meal_id if meal_id is not None else 1

    collector = StatsCollector()
    sizes: list[int] = []

    # Warm-up
    first = report_service.generate_report(session, user_id=uid, meal_id=mid)
    sizes.append(len(first))

    for _ in range(iterations):
        with timer(collector, "pdf_generation"):
            pdf = report_service.generate_report(session, user_id=uid, meal_id=mid)
        sizes.append(len(pdf))

    if own_db:
        session.close()

    metrics = collector.summary()
    avg_size = round(sum(sizes) / len(sizes), 1) if sizes else 0

    rows = [
        [name, v["count"], v["mean_ms"], v["median_ms"], v["p95_ms"]]
        for name, v in metrics.items()
    ]
    write_csv(
        os.path.join(output_dir, "pdf_report.csv"),
        ["metric", "samples", "mean_ms", "median_ms", "p95_ms"],
        rows,
    )

    result = {
        "name": "pdf",
        "iterations": iterations,
        "avg_pdf_size_bytes": avg_size,
        "metrics": metrics,
    }
    write_json(os.path.join(output_dir, "pdf_report.json"), result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark PDF report generation")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=5)
    args = parser.parse_args()
    run_benchmark(output_dir=args.output_dir, iterations=args.iterations)
    print(f"PDF benchmark complete -> {args.output_dir}")
