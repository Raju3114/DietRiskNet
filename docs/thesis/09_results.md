# 09 — Results

The tables below were generated automatically by the evaluation module
(`backend/evaluation/`) into `backend/evaluation/reports/`. They are
representative of the current run configuration: the vision stages used
the harness's fast detector/classifier stubs and the disease-prediction
stage used the real XGBoost models, so the **relative ordering** of the
stages is the meaningful result. Re-run the commands in
[§8.4](08_experimental_setup.md) with real models and a `GEMINI_API_KEY`
to populate production numbers — the module will rewrite the same files.

## 9.1 Pipeline Runtime (Table 5.1)

Source: `backend/evaluation/reports/table_5_1_pipeline_runtime.md`

| Stage | Mean (ms) | Median (ms) | P95 (ms) |
|---|---|---|---|
| yolo_detection | 0.002 | 0.002 | 0.003 |
| efficientnet_classification | 10.386 | 10.386 | 10.422 |
| nutrition_lookup | 0.430 | 0.430 | 0.559 |
| dci | 1.422 | 1.422 | 1.777 |
| nis | 0.022 | 0.022 | 0.025 |
| disease_prediction | 51.438 | 51.438 | 52.831 |
| risk_fusion | 0.005 | 0.005 | 0.006 |
| rule_recommendations | 0.003 | 0.003 | 0.003 |
| **Total (pipeline stages)** | **63.708** | — | — |

**Interpretation**: the fast stages (nutrition, DCI, NIS, fusion, rules)
are sub-millisecond; the XGBoost prediction stage dominates the
deterministic pipeline in this configuration. In a production run the
YOLO + EfficientNet stages dominate (GPU-independent CPU inference).

## 9.2 Cache Performance (Table 5.2)

Source: `backend/evaluation/reports/table_5_2_cache_performance.md`

| Metric | Value |
|---|---|
| Cache hit rate | 50.00% |
| Average cache hit latency (ms) | 0.865 |
| Average cache miss latency (ms) | 2.396 |
| **Latency improvement (hit vs miss)** | **63.90%** |

**Interpretation**: serving a cached AI response is ~2.8× faster than a
miss in this configuration. The improvement grows dramatically when the
miss path includes a real LLM round-trip (Ollama or Gemini, seconds vs.
sub-millisecond).

## 9.3 AI Dietitian Latency (Table 5.3)

Source: `backend/evaluation/reports/table_5_3_ai_latency.md`

| Path | Mean (ms) | Median (ms) | P95 (ms) |
|---|---|---|---|
| ai_cache_hit | 0.865 | 0.865 | ~0.9 |
| ai_cache_miss | 2.396 | 2.396 | ~2.4 |

Average AI response length: **53 characters** (sample summary).
Cache hit rate (synthetic 1:1 mix): **50%**.

## 9.4 PDF Generation (Table 5.4)

Source: `backend/evaluation/reports/table_5_4_pdf_generation.md`

| Metric | Value |
|---|---|
| Mean generation time | ~8.25 ms |
| Average PDF size | ~4,179 bytes |

## 9.5 System Metrics

Source: `backend/evaluation/reports/system_metrics.json`

| Metric | Value |
|---|---|
| Peak traced memory (MB) | 145.2 |
| Current traced memory (MB) | 38.4 |
| RSS (MB) | 210.5 |
| CPU utilisation sample (%) | 3.4 |

> These memory/CPU figures are from the benchmark process itself, not the
> full inference stack. See §8.2 for hardware context.

## 9.6 Quality Assurance

| Check | Result |
|---|---|
| Backend test suite (`backend/tests/`) | 189 passed |
| Frontend type check (`npx tsc --noEmit`) | 0 errors |
| Frontend production build | ✓ compiled |
