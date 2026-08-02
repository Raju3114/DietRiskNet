# DietRiskNet — Final Project Submission Summary

**Project title:** DietRiskNet — Vision-Language-Based Food Recognition and
Personalized Disease-Risk-Aware Dietary Recommendation Using Longitudinal Meal
Analysis

**Type:** Full-stack medical-AI application (final-year capstone)

**Status:** Feature complete · end-to-end validated · ready for submission.

---

## 1. Problem statement

Manual food logging is inaccurate and tedious; existing apps are weak on Indian
food (1,000+ regional dishes); chronic-disease risk is usually assessed in
clinics rather than from everyday meals; and LLMs alone cannot be trusted to
compute nutrition or risk (they hallucinate numbers). No single system combined
food recognition → nutrition → disease-risk prediction → personalised,
grounded advice. DietRiskNet addresses this gap with a **deterministic clinical
core** plus a **grounded, fail-safe AI explanation layer**.

## 2. Objectives

1. Detect and classify foods from a single meal photo (YOLOv8 → EfficientNet-B3).
2. Estimate nutrition from a 1,014-dish Indian food database (11 nutrients each).
3. Compute **DCI** (Dietary Consistency Index) and **NIS** (Nutritional Imbalance Score).
4. Predict diabetes, obesity, hypertension, and deficiency risk with 4 XGBoost models.
5. Fuse all signals into one explainable risk score (Low / Moderate / High / Critical).
6. Explain results and coach the user with a grounded, fail-safe AI layer.
7. Deliver a professional PDF report and an automated benchmarking suite.

## 3. Complete architecture

```
User (photo) → YOLOv8 detection → crop → EfficientNet-B3 classification
  → Indian food nutrition lookup (1,014 dishes × 11 nutrients)
  → DCI / NIS indices → XGBoost ×4 → Weighted Risk Fusion
  → ExplainDiet rule engine → DB persistence → Dashboard / Trends / History / PDF
  → AI Dietitian + Meal Chat + Nutrition Assistant + Personalized Coach
      (via LLM Provider Layer: Ollama default / Gemini optional)
```

- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4,
  Zustand + React Query, Recharts, Framer Motion.
- **Backend:** FastAPI, Pydantic v2, JWT auth, SQLAlchemy (12 tables),
  ReportLab PDF.
- **ML core:** deterministic and reproducible; models are pre-trained.
- **AI layer:** provider-agnostic, optional, fail-safe.

## 4. Technologies used

| Layer | Technologies |
|---|---|
| Backend | Python 3.10, FastAPI 0.139, Pydantic v2, SQLAlchemy 2, Uvicorn |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind v4, Recharts, Zustand, React Query |
| ML | PyTorch (CPU), Ultralytics YOLOv8, EfficientNet-B3/B0, XGBoost, OpenCV, NumPy, Pandas |
| LLM / AI | Provider-agnostic layer — **Ollama (default local)** + **Gemini (optional cloud)** |
| Database | SQLite (dev) / PostgreSQL (Docker) |
| Docs/PDF | ReportLab |
| Deployment | Docker Compose, Render blueprint, Vercel frontend |

## 5. ML models used

| Model | Role | Classes / Notes |
|---|---|---|
| YOLOv8 | Food-region detection | 18 detection classes; per-class IoU 0.6 duplicate suppression |
| EfficientNet-B3 | Crop classification | 118 Indian food classes (B0 fallback; crop sizes 300/224) |
| XGBoost ×4 | Disease-risk prediction | diabetes, obesity, hypertension, deficiency |

**Accuracy note:** these are pre-trained models; the project does **not** claim
retrained or measured mAP/accuracy figures. The evaluation module reports
**latency/memory/cache metrics only** (see §13). No accuracy values are invented
in this document.

## 6. AI / LLM architecture

- `BaseLLMProvider` interface (`enabled`, `generate_json`, `chat`, `generate`,
  `health_check`).
- **`OllamaProvider` (default):** local Ollama server (`localhost:11434`),
  model `llama3.2:3b`, **no API key required**, fully offline.
- **`GeminiProvider` (optional):** Google Gemini cloud; requires `GEMINI_API_KEY`.
- `LLMProviderFactory` selects by `LLM_PROVIDER` (`ollama` default, `gemini`
  optional). `FallbackLLMProvider` automatically retries Gemini failures on
  Ollama.
- `GET /api/ai/health` reports provider, model, status, latency, version.
- Deterministic AI-result cache keyed by SHA-256 context hash + `prompt_version`.

## 7. DCI and NIS

- **DCI** = 1 − coefficient of variation of daily calories over the last 7 days
  (fallback: single-meal macro balance against 55/15/30 carbs/protein/fat
  targets). Classified via a deterministic, order-independent **threshold
  classifier** (0.85 / 0.70 / 0.50).
- **NIS** = mean relative deviation from RDI across six nutrients (Calories,
  Protein, Carbs, Fat, Sodium, Fiber); thresholds 0.2 / 0.4 / 0.6 / 0.8.

## 8. Risk fusion

`Fused = 0.25·(1 − DCI) + 0.25·NIS + 0.20·diabetes + 0.15·obesity
+ 0.10·hypertension + 0.05·deficiency`, bounded to [0,1] → **Low / Moderate /
High / Critical**.

## 9. Recommendation system

- **ExplainDiet rule engine:** threshold-triggered, evidence-backed advice
  (sodium > 800 mg, free sugar > 15 g, calories > 800 kcal, low DCI, risk
  flags) with a "balanced" fallback.
- **Deterministic health score [0–100]** computed by the backend
  (fusion/NIS/DCI/calorie/sodium/sugar/fiber penalties); the LLM only explains it.

## 10. AI Dietitian

Runs after the meal is persisted; consumes only structured ML output; returns
summary, meal quality, deterministic health score/level, risk explanation,
recommendations, healthier alternatives, warnings, follow-up questions.
**Never overrides backend disease-risk values; never breaks the pipeline.**

## 11. Nutrition Assistant

General conversational assistant (meal planning, dietary guidance) that works
even with no meal analysed; reuses stored meal context for personalisation; a
keyword guard deflects off-topic questions without calling the LLM.

## 12. Personalized Coach

Deterministic analytics over the last 14 meals (averages, DCI/NIS, risk trend,
patterns, best/worst meal, smart goals with 0–1 progress); the summary is
injected into the chat context for personalised advice. No ML re-run.

## 13. Ollama integration

Default local provider — verified end-to-end with `llama3.2:3b` (Ollama 0.32.5).
Real generation tested; AI Dietitian latency ~6.7 s (measured); Nutrition
Assistant and Meal Chat produce real replies; offline operation verified (ML
pipeline unaffected, graceful AI fallback, no HTTP 500).

## 14. Database

12 relational tables (`users`, `refresh_tokens`, `user_settings`, `meals`,
`meal_items`, `meal_nutritions`, `disease_predictions`, `risk_fusion_results`,
`recommendations`, `diet_history`, `audit_logs`, `ai_dietitian_results`).
Cascading deletes; composite indexes; SQLAlchemy parameterized queries.

## 15. PDF reporting

ReportLab-generated, multi-section, 2-page PDF (meal image, foods, nutrition,
DCI/NIS, disease risks, fusion, recommendations, AI Dietitian section, footer).
Validated `%PDF-1.4`, generated in ~0.3 s (measured).

## 16. Security

bcrypt password hashing; JWT with `jti` + token-type claims; DB-backed refresh
tokens with revocation; audit logging; upload extension whitelist + UUID
filenames; restricted CORS; `.env` gitignored; **no API keys in source, docs,
or logs**; parameterized SQL; rate-limiting absent (noted limitation).

## 17. Testing

- Backend `pytest`: **169 passed / 0 failed** (includes 20 mocked Ollama
  provider unit tests).
- Frontend `tsc --noEmit`: 0 errors; production build: **17/17 routes**.
- Live E2E: register/login/refresh/revoke, full meal pipeline, AI Dietitian,
  Nutrition Assistant, Coach, Meal Chat, cache miss/hit, PDF, Ollama-offline
  degradation — all verified.

## 18. Final validation results

| Check | Result |
|---|---|
| Backend | ✅ 169 passed / 0 failed |
| Frontend type + build | ✅ PASS |
| YOLO / EfficientNet / Nutrition / DCI / NIS / XGBoost / Fusion / Recommendations | ✅ PASS (meal `Idli` 0.843) |
| AI Dietitian with Ollama | ✅ PASS (deterministic health score 67) |
| Nutrition Assistant / Coach / Meal Chat with Ollama | ✅ PASS (real responses) |
| Cache | ✅ PASS (miss → hit, no re-call) |
| Database / PDF | ✅ PASS |
| Auth / Security | ✅ PASS |
| Gemini required? | ❌ **No** — runs fully on Ollama with no key |

*(Details: `FINAL_OLLAMA_E2E_VALIDATION.md`, `BUG_REPORT.md`.)*

## 19. Contributions

1. End-to-end meal-analysis pipeline (vision → nutrition → risk → advice).
2. Deterministic, order-independent DCI/NIS threshold classifier.
3. Per-class IoU duplicate suppression.
4. AI Dietitian layer with deterministic health score and fail-safe fallback.
5. Persistent, provider-agnostic AI cache.
6. Provider-agnostic LLM layer — **Ollama default, Gemini optional**.
7. Meal-specific chat and Personalized Nutrition Coach from stored history.
8. Professional PDF reports.
9. Automated evaluation/benchmarking module.

## 20. Limitations

- Pre-trained models; no reported retraining or accuracy/mAP (only latency/memory).
- CPU-only inference; several XGBoost features are hardcoded/heuristic inputs.
- No rate limiting; no server-side upload size limit; no Alembic migrations.
- In-memory chat sessions (lost on restart).
- Small local model occasionally returns off-schema JSON → graceful canned reply.
- Frontend logout does not revoke the server-side refresh token (backend
  endpoint exists and is correct; recommended follow-up).

## 21. Future scope

- Retrain/fine-tune YOLO + EfficientNet on larger regional data; report accuracy.
- GPU inference + quantization; portion-size estimation from the image.
- Add OpenAI/Claude/Azure behind the existing provider interface.
- Persist chat sessions (Redis); Alembic migrations; rate limiting.
- Clinical validation on real cohorts.

## 22. Final conclusion

DietRiskNet demonstrates a deterministic clinical-analysis core safely enhanced
by a grounded, provider-agnostic AI layer that runs fully offline on **Ollama**
(default) with **Gemini optional**. It is tested (169 passing tests), built
cleanly, documented end-to-end, and validated live. **Ready for academic
submission and demonstration.**
