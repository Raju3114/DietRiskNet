"""Benchmark the AI result cache (hit vs miss latency, hit rate).

Exercises ``AICacheService`` directly with a controlled mix of cache
hits and misses and reports:

- ``cache_hit`` latency
- ``cache_miss`` latency
- overall cache hit rate
"""

from __future__ import annotations

import argparse
import os
from typing import Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base
from backend.database.models import Meal
from backend.evaluation.system_metrics import (
    DEFAULT_OUTPUT_DIR,
    StatsCollector,
    timer,
    write_csv,
    write_json,
)

CONTEXT = {
    "foods": [{"name": "Vegetable samosa", "calories": 97}],
    "nutrition": {"calories": 97, "sodium": 300},
    "dci": {"score": 0.8, "level": "High"},
    "nis": {"score": 0.3, "level": "Mild"},
    "risk_prediction": {"diabetes_risk": 0.2, "obesity_risk": 0.3,
                        "hypertension_risk": 0.1, "deficiency_risk": 0.2},
    "fusion": {"fused_score": 0.25, "risk_level": "Low"},
    "rule_based_recommendations": [{"category": "General", "content": "Eat well"}],
    "user_profile": {"age": 30},
}

RESPONSE = {
    "summary": "A balanced meal.",
    "meal_quality": "Good",
    "health_score": 80,
    "health_level": "Good",
    "health_explanation": "Fine",
    "risk_explanation": "Low risk.",
    "recommendations": ["Add fiber"],
    "healthier_alternatives": ["Brown rice"],
    "warnings": [],
    "follow_up_questions": [],
}


def _default_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    meal = Meal(user_id=1, image_path="/static/x.png", dci=0.8, nis=0.3)
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return session


def run_benchmark(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    iterations: int = 20,
    db: Optional[object] = None,
) -> Dict[str, float]:
    """Run the cache micro-benchmark.

    ``db`` may be injected (e.g. a test session).  When ``None`` a fresh
    in-memory database is created.
    """
    from backend.services.ai_cache_service import ai_cache_service

    own_db = db is None
    session = db or _default_db()
    collector = StatsCollector()
    hits = 0
    lookups = 0

    # Seed the cache with a known entry.
    seed_hash = ai_cache_service.context_hash(CONTEXT)
    ai_cache_service.save_response(
        session, meal_id=1, provider="gemini", model="bench",
        context=CONTEXT, response=RESPONSE,
    )

    for i in range(iterations):
        if i % 2 == 0:
            # Hit — same context hash.
            lookups += 1
            with timer(collector, "cache_hit"):
                row = ai_cache_service.get_cached_response(
                    session, context_hash=seed_hash, provider="gemini"
                )
            if row is not None:
                hits += 1
        else:
            # Miss — a context hash that was never saved.
            miss_hash = ai_cache_service.context_hash({**CONTEXT, "dci": {"score": 0.9, "level": "High"}})
            lookups += 1
            with timer(collector, "cache_miss"):
                ai_cache_service.get_cached_response(
                    session, context_hash=miss_hash, provider="gemini"
                )

    if own_db:
        session.close()

    metrics = collector.summary()
    hit_rate = round(hits / lookups, 3) if lookups else 0.0

    rows = [
        [name, v["count"], v["mean_ms"], v["median_ms"], v["p95_ms"]]
        for name, v in metrics.items()
    ]
    write_csv(
        os.path.join(output_dir, "cache_report.csv"),
        ["path", "samples", "mean_ms", "median_ms", "p95_ms"],
        rows,
    )

    result = {
        "name": "cache",
        "iterations": iterations,
        "hit_rate": hit_rate,
        "metrics": metrics,
    }
    write_json(os.path.join(output_dir, "cache_report.json"), result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark the AI result cache")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    run_benchmark(output_dir=args.output_dir, iterations=args.iterations)
    print(f"Cache benchmark complete -> {args.output_dir}")
