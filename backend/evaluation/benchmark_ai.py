"""Benchmark the AI Dietitian (cache hit vs cache miss latency).

Measures:
- ``ai_cache_hit``: latency of serving a cached AI response
- ``ai_cache_miss``: latency of the full generation path (LLM call + save)
- average AI response length

By default a deterministic fake LLM client is used so the benchmark runs
without a Gemini key.  When ``GEMINI_API_KEY`` is set, the real Gemini
client is used instead.
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict, Optional

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
from backend.services.llm.base import LLMClient


class _FakeClient(LLMClient):
    """Deterministic stand-in so the benchmark runs without a key."""

    @property
    def enabled(self) -> bool:
        return True

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return {
            "summary": "A balanced meal with good macronutrient distribution.",
            "meal_quality": "Good",
            "risk_explanation": "Low risk across all predicted conditions.",
            "recommendations": ["Add more fiber", "Reduce sodium slightly"],
            "healthier_alternatives": ["Brown rice instead of white"],
            "warnings": [],
            "follow_up_questions": ["What should I eat for dinner?"],
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


ARGS = dict(
    foods=[{"name": "Vegetable samosa", "display_name": "Samosa",
            "weight_g": 100, "calories": 97, "protein": 2, "carbs": 10, "fats": 5}],
    nutrition={"calories": 97, "protein": 2, "carbs": 10, "fats": 5,
               "sodium": 300, "sugar": 3, "fiber": 1},
    dci=0.8, dci_level="High Consistency",
    nis=0.3, nis_level="Mild Imbalance",
    predictions={"diabetes_risk": 0.2, "obesity_risk": 0.3,
                 "hypertension_risk": 0.1, "deficiency_risk": 0.2},
    fusion={"fused_score": 0.25, "risk_level": "Low"},
    rule_recommendations=[{"category": "General", "content": "Eat well"}],
    user_profile={"age": 30},
)


def run_benchmark(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    iterations: int = 3,
    client: Optional[LLMClient] = None,
) -> Dict[str, Any]:
    """Run the AI Dietitian latency benchmark."""
    from backend.services.ai_cache_service import ai_cache_service
    from backend.services.meal_ai_service import MealAIService

    if client is None:
        # By default the benchmark uses the deterministic fake client so
        # results are reproducible without any local/remote provider.
        # Set LLM_BENCHMARK_REAL=1 to measure the configured provider
        # (Ollama by default, Gemini when configured).
        if os.getenv("LLM_BENCHMARK_REAL", "").strip().lower() in (
            "1", "true", "yes",
        ):
            from backend.services.llm.factory import get_llm_client
            real = get_llm_client()
            client = real
            provider = f"{real.name} (real)"
        else:
            client = _FakeClient()
            provider = "fake (deterministic)"

    db = _default_db()
    service = MealAIService(client=client, cache=ai_cache_service)

    collector = StatsCollector()
    response_lengths: list[int] = []

    # Warm-up (cache miss) so the cache is populated.
    warm = service.analyze_meal_cached(
        db, meal_id=1, provider="gemini", model="bench", **ARGS,
    )
    if warm is None:
        # Provider unavailable (real Gemini down) — nothing measurable.
        result = {"name": "ai", "provider": provider, "metrics": {},
                  "avg_response_length": 0, "hit_rate": 0.0,
                  "unavailable": True}
        write_json(os.path.join(output_dir, "ai_report.json"), result)
        db.close()
        return result
    response_lengths.append(len(warm.get("summary", "")))

    # Cache-hit latency.
    for _ in range(iterations):
        with timer(collector, "ai_cache_hit"):
            service.analyze_meal_cached(
                db, meal_id=1, provider="gemini", model="bench", **ARGS,
            )

    # Cache-miss latency (invalidate between calls).
    for _ in range(iterations):
        ai_cache_service.invalidate(db, meal_id=1)
        with timer(collector, "ai_cache_miss"):
            out = service.analyze_meal_cached(
                db, meal_id=1, provider="gemini", model="bench", **ARGS,
            )
            if out:
                response_lengths.append(len(out.get("summary", "")))

    # Hit-rate: mix of repeated (hit) and fresh (miss) lookups.
    hits = 0
    lookups = 0
    for i in range(iterations * 2):
        lookups += 1
        if i % 2 == 0:
            result = service.analyze_meal_cached(
                db, meal_id=1, provider="gemini", model="bench", **ARGS,
            )
            hits += 1 if result is not None else 0
        else:
            ai_cache_service.invalidate(db, meal_id=1)
            service.analyze_meal_cached(
                db, meal_id=1, provider="gemini", model="bench", **ARGS,
            )

    db.close()

    metrics = collector.summary()
    avg_len = (
        round(sum(response_lengths) / len(response_lengths), 1)
        if response_lengths else 0
    )

    rows = [
        [name, v["count"], v["mean_ms"], v["median_ms"], v["p95_ms"]]
        for name, v in metrics.items()
    ]
    write_csv(
        os.path.join(output_dir, "ai_report.csv"),
        ["path", "samples", "mean_ms", "median_ms", "p95_ms"],
        rows,
    )

    result = {
        "name": "ai",
        "provider": provider,
        "iterations": iterations,
        "metrics": metrics,
        "avg_response_length": avg_len,
        "hit_rate": round(hits / lookups, 3) if lookups else 0.0,
    }
    write_json(os.path.join(output_dir, "ai_report.json"), result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark the AI Dietitian")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    run_benchmark(output_dir=args.output_dir, iterations=args.iterations)
    print(f"AI benchmark complete -> {args.output_dir}")
