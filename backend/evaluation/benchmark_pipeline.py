"""Benchmark the ML pipeline stages (detection .. rule recommendations).

Each stage is warmed up once (to exclude model-loading from the steady
state), then timed over *iterations* runs.  Stages that fail (e.g. a
missing model) are recorded as unavailable rather than crashing.

Usage::

    python -m backend.evaluation.benchmark_pipeline --iterations 3
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base
from backend.database.models import User
from backend.evaluation.system_metrics import (
    DEFAULT_OUTPUT_DIR,
    StatsCollector,
    start_memory_tracking,
    stop_memory_tracking,
    timer,
    write_csv,
    write_json,
)

SAMPLE_IMAGE = os.path.join(
    os.path.dirname(__file__), "..", "..", "datasets", "sample_meal.png"
)


def _default_db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    return session


def _ensure_user(db) -> User:
    user = db.query(User).first()
    if user is None:
        user = User(email="bench@test.com", password_hash="x", full_name="Bench")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def run_benchmark(
    output_dir: str = DEFAULT_OUTPUT_DIR,
    iterations: int = 3,
    detector: Optional[Any] = None,
    classifier: Optional[Any] = None,
) -> Dict[str, Any]:
    """Run the pipeline benchmark.

    ``detector`` / ``classifier`` may be injected (e.g. fakes in tests).
    When ``None`` the real services are used.
    """
    from backend.services.indices_services import dci_service, nis_service
    from backend.services.ml_services import classifier_service, detector_service
    from backend.services.nutrition_service import nutrition_service
    from backend.services.prediction_service import prediction_service
    from backend.services.recommendation_service import explain_diet_service
    from backend.services.risk_fusion_service import fusion_service

    detector = detector or detector_service
    classifier = classifier or classifier_service

    collector = StatsCollector()
    start_memory_tracking()

    db = _default_db()
    user = _ensure_user(db)

    nutrition_sample = {
        "calories": 500, "protein": 15, "carbs": 80, "fats": 10,
        "sugar": 2, "fiber": 5, "sodium": 300, "calcium": 50,
        "iron": 2, "vitamin_c": 5, "folate": 20,
    }
    profile = dict(age=30, gender="Male", height=170, weight=70, conditions=[])

    def run_stage(name, fn) -> None:
        try:
            fn()  # warm-up
            for _ in range(iterations):
                with timer(collector, name):
                    fn()
        except Exception as exc:  # model/file missing → record unavailable
            collector.metric(name).add(0.0)  # placeholder; flagged below
            collector.metric(name).samples_ms.clear()
            print(f"  [{name}] unavailable: {type(exc).__name__}: {exc}")

    try:
        detections = detector.detect(SAMPLE_IMAGE)
        crop = detections[0]["box"] if detections else (0, 0, 100, 100)
    except Exception:
        detections = []
        crop = (0, 0, 100, 100)

    # --- per-stage warm-up + timing -------------------------------
    from backend.utils.image_utils import crop_image

    def _detect():
        detector.detect(SAMPLE_IMAGE)

    def _classify():
        crop_bytes = crop_image(SAMPLE_IMAGE, crop)
        classifier.classify(crop_bytes)

    def _nutrition():
        nutrition_service.lookup("vegetable samosa")

    def _dci():
        dci_service.calculate(nutrition_sample, user.id, db)

    def _nis():
        nis_service.calculate(nutrition_sample)

    def _predict():
        prediction_service.predict_all(
            profile["age"], profile["gender"], profile["height"],
            profile["weight"], nutrition_sample, profile["conditions"],
        )

    def _fusion():
        fusion_service.fuse(0.8, 0.3, 0.2, 0.3, 0.1, 0.2)

    def _rules():
        explain_diet_service.recommend(nutrition_sample, {
            "diabetes_risk": 0.2, "obesity_risk": 0.3,
            "hypertension_risk": 0.1, "deficiency_risk": 0.2,
        }, 0.8, 0.3)

    run_stage("yolo_detection", _detect)
    run_stage("efficientnet_classification", _classify)
    run_stage("nutrition_lookup", _nutrition)
    run_stage("dci", _dci)
    run_stage("nis", _nis)
    run_stage("disease_prediction", _predict)
    run_stage("risk_fusion", _fusion)
    run_stage("rule_recommendations", _rules)

    try:
        prediction_service.unload()
    except Exception:
        pass
    try:
        detector.unload()
    except Exception:
        pass
    try:
        classifier.unload()
    except Exception:
        pass
    db.close()

    memory = stop_memory_tracking()
    metrics = collector.summary()

    # CSV report
    rows = [
        [name, v["count"], v["mean_ms"], v["median_ms"], v["p95_ms"]]
        for name, v in metrics.items()
    ]
    write_csv(
        os.path.join(output_dir, "pipeline_report.csv"),
        ["stage", "samples", "mean_ms", "median_ms", "p95_ms"],
        rows,
    )

    result = {
        "name": "pipeline",
        "iterations": iterations,
        "memory_mb": memory,
        "metrics": metrics,
        "detections": len(detections),
    }
    write_json(os.path.join(output_dir, "pipeline_report.json"), result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark the ML pipeline")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--iterations", type=int, default=3)
    args = parser.parse_args()
    run_benchmark(output_dir=args.output_dir, iterations=args.iterations)
    print(f"Pipeline benchmark complete -> {args.output_dir}")
