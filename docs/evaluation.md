# DietRiskNet — Evaluation & Benchmarking

This document explains how to run the performance benchmarks, how each
metric is computed, and how to interpret the generated reports for the
thesis / dissertation.

---

## 1. Running the Benchmarks

Activate the backend virtual environment first, then run any benchmark
from the project root:

```bash
# Activate venv
backend/.venv\Scripts\activate.bat        # Windows CMD
source backend/.venv/bin/activate          # macOS / Linux

# Run a single benchmark
python -m backend.evaluation.benchmark_pipeline --iterations 3
python -m backend.evaluation.benchmark_ai      --iterations 3
python -m backend.evaluation.benchmark_cache   --iterations 20
python -m backend.evaluation.benchmark_pdf     --iterations 5

# Run everything and generate CSV + JSON + charts + thesis tables
python -m backend.evaluation.system_metrics --iterations 3
```

All outputs are written to `backend/evaluation/reports/` by default
(override with `--output-dir`).

### Output files

| Type | Files |
|------|-------|
| CSV | `pipeline_report.csv`, `ai_report.csv`, `cache_report.csv`, `pdf_report.csv` |
| JSON | `pipeline_report.json`, `ai_report.json`, `cache_report.json`, `pdf_report.json`, `system_metrics.json` |
| Charts | `pipeline_latency.png`, `cache_performance.png`, `ai_latency.png`, `memory_usage.png`, `pdf_generation.png` |
| Thesis tables | `table_5_1_pipeline_runtime.md`, `table_5_2_cache_performance.md`, `table_5_3_ai_latency.md`, `table_5_4_pdf_generation.md` |

---

## 2. What each benchmark measures

### `benchmark_pipeline` — ML pipeline stages

Times each stage independently (after a warm-up pass so model loading is
excluded):

| Stage | Backend component |
|-------|-------------------|
| `yolo_detection` | `FoodDetectionService.detect` |
| `efficientnet_classification` | `FoodClassificationService.classify` (first crop) |
| `nutrition_lookup` | `NutritionService.lookup` |
| `dci` | `DCIService.calculate` |
| `nis` | `NISService.calculate` |
| `disease_prediction` | `DiseasePredictionService.predict_all` (4 × XGBoost) |
| `risk_fusion` | `RiskFusionService.fuse` |
| `rule_recommendations` | `ExplainDietService.recommend` |

Uses `datasets/sample_meal.png`. If a model file is missing, that stage
is reported as unavailable instead of failing.

### `benchmark_ai` — AI Dietitian latency

- `ai_cache_hit` — serving a previously cached AI response
- `ai_cache_miss` — full generation path (LLM call + cache write)
- `avg_response_length` — mean length of the AI summary in characters
- `hit_rate` — fraction of lookups served from cache in the synthetic mix

By default a deterministic **fake** LLM client is used so the benchmark
runs without a Gemini key.  If `GEMINI_API_KEY` is set in the
environment, the **real** Gemini client is used (set the key and run
again for production numbers).

### `benchmark_cache` — result cache

Direct micro-benchmark of `AICacheService`:
- `cache_hit` — `get_cached_response` for a known context hash
- `cache_miss` — `get_cached_response` for a context hash never saved
- `hit_rate` — hits ÷ total lookups (synthetic 1:1 mix)

### `benchmark_pdf` — report generation

- `pdf_generation` — `ReportService.generate_report` latency
- `avg_pdf_size_bytes` — mean generated PDF size

### `system_metrics` — aggregate + charts + tables

Runs all four benchmarks, measures Python process memory (peak traced
memory + RSS), CPU utilisation (via `psutil`, when available), writes
`system_metrics.json`, and renders the PNG charts and markdown thesis
tables.

---

## 3. How the metrics are computed

Each stage is timed with a high-resolution `time.perf_counter` and
recorded in milliseconds.  After `N` runs the framework reports:

| Statistic | Definition |
|-----------|------------|
| **Mean** | arithmetic mean of the sample |
| **Median** | 50th percentile — robust to outliers |
| **P95** | 95th percentile (nearest-rank) — worst-case view |

**Memory** is measured with `tracemalloc` (current + peak Python heap,
MB) and, when available, `psutil` RSS.  **CPU** is a single
`psutil.cpu_percent()` sample taken during `run_all`.

Charts are rendered with matplotlib (Agg backend) and are PNG at 120 dpi.

---

## 4. Interpreting the results

- **Pipeline latency**: dominated by `yolo_detection` and
  `efficientnet_classification` (vision inference).  The fast stages
  (nutrition lookup, DCI/NIS, fusion, rules) should be well under a few
  milliseconds.  High P95 vs mean indicates cold-start variance.
- **AI latency**: `ai_cache_miss` is the real LLM round-trip;
  `ai_cache_hit` should be tens of times faster.  The difference is the
  value of caching.  Use **Table 5.2** (`improvement`) to report it.
- **Cache hit rate**: in production this depends on how often identical
  meals are re-analysed; the benchmark's 50% mix is a synthetic
  baseline.
- **PDF generation**: typically a few milliseconds for a single meal;
  size reflects the number of items and the embedded sections.
- **Memory**: peak traced memory during `run_all` reflects the Python
  heap; RSS adds model/library resident memory.

---

## 5. Reproducibility notes

- The vision stages load real weights from `backend/trained_models/` on
  first use; the warm-up pass excludes load time from the numbers.
- Runs are single-threaded CPU inference (Render free-tier class).
- For stable thesis numbers, run with `--iterations 5` or higher and
  take the median across multiple invocations.
- Set `GEMINI_API_KEY` to benchmark real AI latency; otherwise the AI
  benchmark reports the deterministic fake client.
