# 10 — Discussion

## 10.1 Advantages

- **Deterministic clinical core.** YOLO, EfficientNet, nutrition, DCI,
  NIS, XGBoost and risk fusion form a fully deterministic pipeline. The
  same meal always yields the same risk output, which is essential for a
  medical-adjacent tool.
- **Threshold-based indices.** DCI/NIS classification no longer depends
  on JSON iteration order; boundary values are unambiguous and validated
  at startup (fail-fast).
- **Duplicate suppression.** A per-class IoU filter prevents a single
  dish from being counted twice in the UI and calorie totals.
- **Clean AI separation.** The LLM (Ollama by default, Gemini optional)
  only *explains* structured ML output —
  it never performs detection, classification, or prediction. A
  deterministic health score is computed locally; the LLM merely adds a
  human-readable narrative.
- **Fail-safe AI.** Missing API key, timeout, quota, or bad JSON never
  breaks the meal analysis: `ai_dietitian = null` and rule-based
  recommendations stand. The project never returns HTTP 500 because of
  the LLM provider.
- **Caching.** Identical contexts are never sent to the LLM twice;
  `context_hash` covers every input that could change the answer.
- **Provider abstraction.** The `LLMClient` interface allows OpenAI,
  Claude, Ollama, or Azure OpenAI to be added without touching business
  logic.
- **Comprehensive evaluation.** The benchmarking module produces CSV,
  JSON, charts, and dissertation-ready tables, making results
  reproducible and thesis-friendly.
- **Portable deployment.** SQLite for dev, PostgreSQL for Docker/Render,
  a single `docker-compose` command, and a `render.yaml` blueprint.

## 10.2 Limitations

- **Models are pre-trained and fixed.** No retraining pipeline is
  included; the YOLO/EfficientNet/XGBoost weights are treated as
  ground truth.
- **CPU-only inference.** `torch.set_num_threads(1)` bounds performance
  to a single core (matching Render's free tier); GPU acceleration is
  not exploited.
- **Vision benchmark stubs.** The current sample reports use fast
  detector/classifier stubs; real vision latency requires the actual
  weights (see §9).
- **Rule engine is shallow.** Recommendations are threshold-triggered
  and do not use longitudinal patterns beyond DCI.
- **Chat memory is in-memory.** Conversations are lost on server restart
  and do not scale horizontally across workers.
- **No Alembic migrations.** Schema changes rely on
  `create_all`, which does not alter existing tables.
- **AI output is unverified.** The LLM narrative is only
  instruction-constrained; it is not clinically validated.

## 10.3 Future Work

- Add a model retraining / fine-tuning pipeline for Indian-food
  detection and classification.
- GPU inference and model quantization for lower latency.
- Real `GEMINI_API_KEY` benchmarking and prompt-version tuning.
- Add OpenAI / Claude / Ollama providers behind the existing
  `LLMClient` interface.
- Persist chat sessions (bounded) and scale the session store.
- Integrate Alembic migrations.
- Expand the rule engine with longitudinal trends and serving-size
  estimation from the image.
- Add rate limiting and admin dashboards for production hardening.
