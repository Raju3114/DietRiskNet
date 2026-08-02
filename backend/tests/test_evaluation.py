"""Tests for the evaluation / benchmarking module.

Covers:
- StatsCollector statistics (mean, median, p95)
- CSV / JSON report writers
- benchmark smoke tests (cache, pdf, ai, pipeline with fakes)
- chart generation (PNG)
- thesis table generation (markdown)
"""

import json
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.database import Base
# Import models so Base.metadata.create_all() includes every table
# (e.g. ai_dietitian_results) used by the benchmarks.
import backend.database.models  # noqa: F401, E402
from backend.evaluation.system_metrics import (
    DEFAULT_OUTPUT_DIR,
    StatsCollector,
    generate_charts,
    generate_thesis_tables,
    timer,
    write_csv,
    write_json,
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


class TestStatsCollector:
    def test_mean_median_p95(self):
        c = StatsCollector()
        for v in [10, 20, 30, 40, 100]:
            c.sample("m", float(v))
        m = c.metric("m")
        assert m.count == 5
        assert m.mean_ms == 40.0
        assert m.median_ms == 30.0
        # nearest-rank p95 of sorted [10,20,30,40,100] at idx 4 = 100
        assert m.p95_ms == 100.0

    def test_empty_metric(self):
        c = StatsCollector()
        m = c.metric("empty")
        assert m.count == 0
        assert m.mean_ms == 0.0
        assert m.median_ms == 0.0
        assert m.p95_ms == 0.0

    def test_timer_context_manager(self):
        c = StatsCollector()
        with timer(c, "fast"):
            pass
        assert c.metric("fast").count == 1
        assert c.metric("fast").mean_ms >= 0.0


class TestReportWriters:
    def test_write_csv_and_json(self, tmp_path):
        csv_path = os.path.join(str(tmp_path), "x.csv")
        json_path = os.path.join(str(tmp_path), "x.json")

        write_csv(csv_path, ["a", "b"], [[1, 2], [3, 4]])
        write_json(json_path, {"a": 1, "b": [1, 2]})

        assert os.path.exists(csv_path)
        with open(csv_path, encoding="utf-8") as f:
            content = f.read()
        assert "a,b\n1,2\n3,4\n" in content

        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        assert data == {"a": 1, "b": [1, 2]}


class _FakeDetector:
    def detect(self, path):
        return [{"name": "food", "confidence": 0.9, "box": (10, 10, 100, 100)}]

    def unload(self):
        pass


class _FakeClassifier:
    def classify(self, crop_bytes):
        return {"class_name": "vegetable_samosa", "confidence": 0.9}

    def unload(self):
        pass


class TestBenchmarkSmoke:
    def test_cache_benchmark(self, tmp_path, db):
        from backend.evaluation.benchmark_cache import run_benchmark
        result = run_benchmark(output_dir=str(tmp_path), iterations=4, db=db)
        assert result["hit_rate"] == 0.5
        assert "cache_hit" in result["metrics"]
        assert "cache_miss" in result["metrics"]
        assert os.path.exists(os.path.join(str(tmp_path), "cache_report.csv"))
        assert os.path.exists(os.path.join(str(tmp_path), "cache_report.json"))

    def test_pdf_benchmark(self, tmp_path, db):
        from backend.evaluation.benchmark_pdf import run_benchmark
        result = run_benchmark(output_dir=str(tmp_path), iterations=3)
        assert result["avg_pdf_size_bytes"] > 1000
        assert "pdf_generation" in result["metrics"]
        assert os.path.exists(os.path.join(str(tmp_path), "pdf_report.csv"))

    def test_ai_benchmark(self, tmp_path, db, monkeypatch):
        from backend.evaluation.benchmark_ai import run_benchmark
        # Force the deterministic fake LLM client so this smoke test is
        # independent of whether a real GEMINI_API_KEY is configured in
        # the local .env (otherwise it would attempt a real LLM call).
        from backend.config import settings
        monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
        result = run_benchmark(output_dir=str(tmp_path), iterations=2)
        assert result["avg_response_length"] > 0
        assert "ai_cache_hit" in result["metrics"]
        assert os.path.exists(os.path.join(str(tmp_path), "ai_report.json"))

    def test_pipeline_benchmark_with_fakes(self, tmp_path, db):
        from backend.evaluation.benchmark_pipeline import run_benchmark
        result = run_benchmark(
            output_dir=str(tmp_path),
            iterations=2,
            detector=_FakeDetector(),
            classifier=_FakeClassifier(),
        )
        assert "yolo_detection" in result["metrics"]
        assert "rule_recommendations" in result["metrics"]
        assert os.path.exists(os.path.join(str(tmp_path), "pipeline_report.json"))


class TestChartsAndTables:
    def test_generate_charts(self, tmp_path):
        results = {
            "pipeline": {
                "metrics": {
                    "yolo_detection": {"mean_ms": 5.0, "median_ms": 4.0, "p95_ms": 9.0},
                    "disease_prediction": {"mean_ms": 20.0, "median_ms": 18.0, "p95_ms": 30.0},
                }
            },
            "cache": {
                "hit_rate": 0.5,
                "metrics": {
                    "cache_hit": {"mean_ms": 0.5},
                    "cache_miss": {"mean_ms": 3.0},
                },
            },
            "ai": {"metrics": {"ai_cache_hit": {"mean_ms": 0.4}, "ai_cache_miss": {"mean_ms": 250.0}}},
            "system": {"memory": {"peak_mb": 120.0}},
            "pdf": {"metrics": {"pdf_generation": {"mean_ms": 8.0}}},
        }
        charts = generate_charts(results, str(tmp_path))
        assert any("pipeline_latency.png" in c for c in charts)
        assert any("cache_performance.png" in c for c in charts)
        assert any("ai_latency.png" in c for c in charts)
        assert any("memory_usage.png" in c for c in charts)
        assert any("pdf_generation.png" in c for c in charts)

    def test_generate_thesis_tables(self, tmp_path):
        def metric(mean, median, p95):
            return {"mean_ms": mean, "median_ms": median, "p95_ms": p95}

        results = {
            "pipeline": {
                "metrics": {
                    "yolo_detection": metric(5.0, 4.0, 9.0),
                    "disease_prediction": metric(20.0, 18.0, 30.0),
                }
            },
            "cache": {
                "hit_rate": 0.5,
                "metrics": {
                    "cache_hit": metric(0.5, 0.4, 0.9),
                    "cache_miss": metric(3.0, 2.5, 5.0),
                },
            },
            "ai": {
                "metrics": {
                    "ai_cache_hit": metric(0.4, 0.4, 0.6),
                    "ai_cache_miss": metric(250.0, 230.0, 400.0),
                }
            },
            "pdf": {
                "avg_pdf_size_bytes": 4000,
                "metrics": {"pdf_generation": metric(8.0, 7.0, 10.0)},
            },
        }
        tables = generate_thesis_tables(results, str(tmp_path))
        names = [os.path.basename(t) for t in tables]
        assert "table_5_1_pipeline_runtime.md" in names
        assert "table_5_2_cache_performance.md" in names
        assert "table_5_3_ai_latency.md" in names
        assert "table_5_4_pdf_generation.md" in names

        with open(os.path.join(str(tmp_path), "table_5_2_cache_performance.md"), encoding="utf-8") as f:
            content = f.read()
        assert "Cache hit rate" in content
        assert "Latency improvement" in content
