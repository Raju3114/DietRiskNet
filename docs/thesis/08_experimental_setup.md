# 08 — Experimental Setup

## 8.1 Dataset

| Data | Source / contents | Location |
|------|-------------------|----------|
| Nutrition database | 1,014 Indian dishes × 11 nutrient fields | `nutrition/indian_food_nutrition_processed.csv` |
| Food classes | 118 classes used by EfficientNet | `backend/trained_models/efficientnet_classes.json` |
| Detection classes | 18 classes used by YOLOv8 | embedded in `DietRiskNet_FoodDetector_YOLOv8.pt` |
| Evaluation image | `datasets/sample_meal.png` (used by the pipeline benchmark) | `datasets/sample_meal.png` |
| Synthetic AI benchmark | Deterministic fake LLM client (default; set `LLM_BENCHMARK_REAL=1` to use the real configured provider — Ollama by default) | `backend/evaluation/benchmark_ai.py` |

**Models (pre-trained, not retrained in this work):**

| Model | File | Size |
|-------|------|------|
| YOLOv8 detector | `DietRiskNet_FoodDetector_YOLOv8.pt` | ~22 MB |
| EfficientNet-B3 classifier | `DietRiskNet_FoodClassifier_EfficientNetB3.pth` | ~126 MB |
| EfficientNet-B0 classifier (fallback) | `DietRiskNet_FoodClassifier_EfficientNetB0.pth` | ~18 MB |
| XGBoost ×4 | `*_XGBoost.pkl` (diabetes, obesity, hypertension, deficiency) | 0.6–2.8 MB |

## 8.2 Hardware

Benchmarks in this study were run on:

| Component | Specification |
|-----------|---------------|
| CPU | Intel (single-node, multi-core) |
| RAM | sufficient to hold the ~126 MB classifier + ~22 MB detector in memory |
| GPU | None — inference is CPU-only (`torch.set_num_threads(1)`), matching the Render free-tier class |

*Note: exact timings are hardware-dependent. The evaluation module
reports mean / median / p95 so results are reproducible across runs.*

## 8.3 Software

| Layer | Version |
|-------|---------|
| Python | 3.10 |
| FastAPI | 0.139 |
| Next.js | 16.2 |
| React | 19.2 |
| PyTorch | 2.5.1 (CPU) |
| Ultralytics | 8.4 |
| XGBoost | 3.2 |
| SQLAlchemy | 2.0 |
| ReportLab | 5.0 |
| google-generativeai | 0.8 |
| matplotlib | 3.10 |

Dependencies are pinned in `requirements.txt` and `frontend/package.json`.

## 8.4 Evaluation Metrics

Measured by `backend/evaluation/`:

| Metric | Definition |
|--------|------------|
| Mean latency | arithmetic mean of per-stage timings (ms) |
| Median latency | 50th percentile (robust) |
| P95 latency | 95th percentile (worst-case view) |
| Memory | `tracemalloc` current + peak (MB) + `psutil` RSS |
| CPU utilisation | `psutil.cpu_percent` sample |
| Cache hit rate | hits ÷ lookups in the synthetic mix |
| Avg AI response length | mean length (chars) of the AI summary |
| Avg PDF size | mean bytes of generated PDF |

**How to run:**

```bash
python -m backend.evaluation.benchmark_pipeline --iterations 5
python -m backend.evaluation.benchmark_ai      --iterations 5
python -m backend.evaluation.benchmark_cache   --iterations 20
python -m backend.evaluation.benchmark_pdf     --iterations 5
python -m backend.evaluation.system_metrics    --iterations 5   # all + charts + tables
```

Outputs → `backend/evaluation/reports/`.

## 8.5 Reproducibility notes

- Vision stages are warmed up once so model-loading time is excluded.
- Single-threaded CPU inference is used throughout.
- For the AI benchmark, set `LLM_BENCHMARK_REAL=1` to measure the real
  configured provider (Ollama by default); otherwise a deterministic fake
  client is used so results are reproducible without a live model.
