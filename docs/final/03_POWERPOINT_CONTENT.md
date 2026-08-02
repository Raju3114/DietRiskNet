# DietRiskNet — 15-Slide Presentation Content

*Presentation-ready script for the final project defence. Target: ~15 minutes
(~1 minute per slide) plus Q&A.*

**Design language suggestion:** consistent dark clinical palette — deep
charcoal background, blue/emerald/cyan accents (matching the app), a clean
sans-serif font, one full-bleed screenshot per demo slide. Every fact below is
verified against the repository.

---

## Slide 1 — Title

**Title:** DietRiskNet — Vision-Language Food Recognition & Personalized Disease-Risk-Aware Dietary Recommendation

**Subtitle:** A Full-Stack Medical-AI System for Meal Analysis, Disease-Risk Prediction, and AI-Guided Nutrition

**Bullet points:**
- Final-Year Project — [Your Name], [Roll No]
- [Department], [University], [Academic Year]
- Supervisor: [Supervisor Name]

**Detailed explanation:**
Opening slide that names the project and frames it as a complete, deployable
product, not a single model. The tagline captures the three pillars: **computer
vision** (recognises food from a photo), **clinical ML** (predicts disease
risk), and a **grounded AI coach** (explains and personalises the advice).

**Speaker notes:**
"Good morning. I present DietRiskNet — an end-to-end system that photographs a
meal, recognises every dish with computer vision, computes its nutrition,
predicts disease risk with machine learning, and uses an AI assistant to
explain and personalise the advice. Everything you will see today is running,
tested, and documented."

**Suggested screenshots:** full landing page (`http://localhost:3000`).

**Timing:** 0:15

---

## Slide 2 — Problem Statement

**Title:** The Problem

**Bullet points:**
- Manual food logging is tedious and inaccurate — users underestimate portions and nutrients.
- Existing apps are weak on **Indian food** — 1,000+ regional dishes are missing or mislabelled.
- Chronic-disease risk is usually assessed in clinics, not from everyday meals.
- LLMs alone cannot be trusted to *compute* nutrition or risk — they hallucinate numbers.
- No single system combines food recognition → nutrition → disease risk → personalised advice.

**Detailed explanation:**
Frame the gap on two axes. **Accuracy:** generic apps and LLMs give plausible but
wrong numbers for regional diets. **Completeness:** no tool closes the loop from
a photo of a meal to an explainable disease-risk assessment. DietRiskNet answers
both by building a *deterministic* analysis core and layering a *grounded,
fail-safe* AI on top.

**Speaker notes:**
"Existing food apps are weak on Indian dishes, and LLMs hallucinate numbers.
So we built a system where the analysis is deterministic and reproducible — and
the AI only explains verified results, never computes them."

**Suggested screenshots:** no screenshot — use a 4-icon problem graphic (food log, regional diet, clinical risk, LLM).

**Timing:** 0:45

---

## Slide 3 — Objectives

**Title:** Objectives

**Bullet points:**
- Detect and classify foods from a single meal photo (YOLOv8 → EfficientNet).
- Estimate nutrition from a **1,014-dish Indian food database** (11 nutrients each).
- Compute **Dietary Consistency Index (DCI)** and **Nutritional Imbalance Score (NIS)**.
- Predict **diabetes, obesity, hypertension, and deficiency** risk with 4 XGBoost models.
- Fuse all signals into **one explainable risk score** (Low / Moderate / High / Critical).
- Explain results and coach the user with a **grounded, fail-safe AI layer**.
- Deliver a **professional PDF report** and an automated **benchmarking suite**.

**Detailed explanation:**
Map each objective to a delivered, verifiable component — each has a UI page, a
DB table, or a report. This makes the objectives demonstrable live rather than
aspirational.

**Speaker notes:**
"All seven objectives are implemented and demoable. A key design rule: the AI
layer can enhance, but can never override, the deterministic analysis."

**Suggested screenshots:** no screenshot — a numbered objective list graphic.

**Timing:** 0:45

---

## Slide 4 — Literature Survey

**Title:** Literature Survey

**Bullet points:**
- **Detection — YOLO family** (Redmon et al.; Ultralytics YOLOv8): one-stage, real-time detection.
- **Classification — EfficientNet** (Tan & Le, 2019): compound-scaled CNNs, high accuracy per FLOP.
- **Tabular risk — XGBoost** (Chen & Guestrin, 2016): gradient-boosted trees for structured health features.
- **Nutrition data — national food-composition tables**: Indian food-composition databases mapped to a machine-readable CSV.
- **LLMs in health — grounded/retrieval generation**: LLMs are used to *explain*, not to compute nutrition or risk.
- **Gap:** no prior work integrates regional food vision + disease-risk ML + grounded LLM coaching into one deployable system.

**Detailed explanation:**
Show that the individual techniques are established; the **novelty is the
integration** — the deterministic index classifier and the fail-safe grounding
of the LLM on computed numbers.

**Speaker notes:**
"The models are state of the art but well known. My contribution is how they
are integrated, how the DCI/NIS indices are made deterministic, and how the LLM
is kept grounded and safe."

**Suggested screenshots:** no screenshot — a 2×3 citation grid.

**Timing:** 1:00

---

## Slide 5 — System Architecture

**Title:** System Architecture

**Bullet points:**
- **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind v4, Framer Motion, Zustand + React Query, Recharts.
- **Backend:** FastAPI 0.139, Python 3.10, Pydantic v2, JWT auth, SQLAlchemy — **12 tables** across **8 API routers**.
- **ML core:** YOLOv8 → EfficientNet-B3 (B0 fallback) → nutrition CSV → DCI/NIS → XGBoost ×4 → risk fusion → rule engine.
- **AI layer:** provider-agnostic `LLMClient` (Gemini active) with **SHA-256 context-hash caching**.
- **Data & delivery:** PostgreSQL (Docker) / SQLite fallback; ReportLab PDF; in-memory conversation store; benchmark module.
- **Deployment:** Docker Compose locally; **Vercel** frontend + **Render** backend (CPU-only inference).

**Detailed explanation:**
Walk the diagram top-to-bottom: the browser calls FastAPI; the ML pipeline is
deterministic and persisted to the database; the AI layer is optional and
fail-safe. Every box maps to a real module in the repository.

**Speaker notes:**
"Every box here is a real module. The key design decision is the separation of
concerns: the deterministic core computes, the AI explains."

**Suggested screenshots:** the Mermaid architecture diagram from
`docs/thesis/01_system_architecture.md`.

**Timing:** 1:00

---

## Slide 6 — ML Pipeline: Food Detection & Classification (Vision)

**Title:** Food Detection & Classification

**Bullet points:**
- **YOLOv8** localises food regions → bounding boxes + confidence (18 food-related detection classes).
- **Per-class IoU filter (0.6)** removes duplicate boxes — one dish is never counted twice.
- Each crop → **EfficientNet-B3** → one of **118 Indian dishes** (EfficientNet-B0 as fallback).
- Pre-trained models (not retrained in this work): YOLO ~22 MB, EfficientNet-B3 ~126 MB, B0 ~18 MB.
- Results rendered as bounding-box overlays and per-segment food cards.

**Detailed explanation:**
Explain the cascade and the duplicate-suppression step. The IoU filter keeps
calorie totals honest — without it, overlapping detections would double-count a
single dish.

**Speaker notes:**
"YOLO localises, EfficientNet classifies. The IoU filter is important: it stops
one dish being counted twice in the calories. Inference is CPU-only, which
matches our free-tier deployment."

**Suggested screenshots:** the **Analysis page** with bounding boxes + segment cards.

**Timing:** 1:00

---

## Slide 7 — Nutrition Engine: Lookup + DCI + NIS

**Title:** Nutrition Analysis and Indices

**Bullet points:**
- Lookup over **1,014 Indian dishes × 11 nutrients** — matching order: exact → alias → deterministic normalisation → fuzzy.
- Per-item nutrition scaled by serving weight (default 100 g) and aggregated across the meal.
- **DCI** = 1 − coefficient of variation of daily calories (longitudinal); thresholds **0.85 / 0.70 / 0.50**.
- **NIS** = mean relative deviation from Recommended Daily Intake; thresholds **0.2 / 0.4 / 0.6 / 0.8**.
- Threshold classifier is deterministic and **order-independent** — no boundary ambiguity (a score always maps to exactly one level).

**Detailed explanation:**
Explain the two indices. Highlight the design improvement: the previous
implementation used overlapping interval ranges (0.85 matched two levels,
depends on dict order); the new threshold-point classifier makes classification
provably unique. NIS compares against a fixed RDI (2000 kcal, 60 g protein,
300 g carbs, 65 g fat, 2300 mg sodium, 30 g fibre).

**Speaker notes:**
"These indices are the clinical brain of the analysis. I replaced overlapping
interval ranges with threshold points, so a score like 0.85 always maps to
exactly one level — the classification is deterministic."

**Suggested screenshots:** **Dashboard DCI/NIS cards** + nutrition tiles.

**Timing:** 1:00

---

## Slide 8 — ML Pipeline: Disease Prediction + Risk Fusion

**Title:** Disease Risk Prediction & Fusion

**Bullet points:**
- **Four XGBoost classifiers:** diabetes, obesity, hypertension, deficiency (0.6–2.8 MB each).
- Features: age, gender, BMI, existing conditions, engineered dietary metrics.
- Weighted fusion formula:
  `0.25·(1 − DCI) + 0.25·NIS + 0.20·Diabetes + 0.15·Obesity + 0.10·Hypertension + 0.05·Deficiency`
- Bounded to [0, 1] → levels: **≤ 0.25 Low · ≤ 0.50 Moderate · ≤ 0.75 High · else Critical**.
- Result stored per meal in `risk_fusion_results`, shown on predictions, dashboard, and PDF.

**Detailed explanation:**
Show the formula and the four-level scale. A consistent diet (high DCI) lowers
risk via the `1 − DCI` term; the fused score is a single explainable number for
the whole meal.

**Speaker notes:**
"Four models give four probabilities. The fusion formula combines them with the
indices into one bounded, explainable score with a four-level risk label."

**Suggested screenshots:** **Predictions page** (four gauges + fused score).

**Timing:** 1:00

---

## Slide 9 — Rule Recommendations + AI Dietitian

**Title:** From Rules to AI Explanations

**Bullet points:**
- **ExplainDiet rule engine:** threshold-triggered, evidence-backed advice — e.g. sodium > 800 mg → reduce salt; free sugar > 15 g → whole grains & low-GI; calories > 800 kcal → portion control; low DCI → consistent meal timing.
- **Deterministic health score [0–100]** computed by the backend (fused-risk penalty up to 30 points) — the AI only explains it.
- **AI Dietitian (Gemini):** summary, meal-quality rating, risk explanation, healthier alternatives, warnings.
- **Fail-safe:** missing API key / timeout / malformed JSON → `ai_dietitian: null`, rule engine stands. **Never a 500.**

**Detailed explanation:**
Contrast deterministic rules with the LLM explanation. This fail-safe design is
a key differentiator: the AI is an enhancement, never a dependency.

**Speaker notes:**
"The health score is computed by my code, not Gemini. If Gemini fails or times
out, the analysis still succeeds — the AI explains verified numbers, and the
rules always stand."

**Suggested screenshots:** **Recommendations page** + the **AI Dietitian card** on the Analysis page.

**Timing:** 1:00

---

## Slide 10 — AI Modules: Meal Chat + Nutrition Assistant

**Title:** Conversational AI

**Bullet points:**
- **Meal-specific chat** grounded in one persisted meal — it never re-runs the ML models.
- Rolling **10-message** in-memory history per (user, meal).
- **Nutrition Assistant:** general nutrition coaching that works with zero analysed meals.
- Off-topic questions (politics, movies, …) → polite canned reply, **no LLM call**.
- Provider-agnostic `LLMClient` (Gemini today; OpenAI / Claude / Ollama / Azure swappable in `factory.get_llm_client`).

**Detailed explanation:**
Show the chat UI and explain grounding + memory + provider abstraction. Adding a
provider requires one new module and one factory branch — no business-logic
changes.

**Speaker notes:**
"The chat loads the stored analysis — it never re-runs the models — and the
provider sits behind an interface, so the system is not tied to Gemini."

**Suggested screenshots:** **AI chat panel** on the Analysis page + the **Nutrition Coach chat** on the Nutrition page.

**Timing:** 1:00

---

## Slide 11 — Personalized Nutrition Coach

**Title:** Personalized Nutrition Coach

**Bullet points:**
- Deterministic analytics over the **last 14 meals**: average calories, protein, sodium, fibre, DCI/NIS, risk trend.
- **Pattern detection** over a 5-meal window — e.g. "high sodium in 4 of your last 5 meals", low protein, low fibre.
- **Smart goals** with 0–1 progress: reduce sodium, increase protein/fibre, consistency, balance, hydration.
- **Weekly summary** + quick actions (Meal Plan, Grocery List, Hydration, Improve Diet).
- Coach summary injected into the chat context for personalised, grounded advice.

**Detailed explanation:**
Show the dashboard and explain why the analytics are deterministic —
reproducible, free, and incapable of hallucination. Gemini writes only the
narrative around these verified numbers.

**Speaker notes:**
"This dashboard is pure aggregation from the database — no LLM involved. Gemini
only turns these verified numbers into a personalised narrative."

**Suggested screenshots:** **Nutrition page** dashboard — stat tiles, pattern cards, goal progress bars.

**Timing:** 1:00

---

## Slide 12 — Results & User Interface

**Title:** Results & User Interface

**Bullet points:**
- Full flow works live: **register → upload → analysis → predictions → recommendations → AI → PDF**.
- **PDF report:** meal image, detected foods, nutrition summary, health analysis, AI Dietitian section, footer — generated with ReportLab.
- **History** log and **7 / 14 / 30-day trends**.
- **Dashboard:** today's intake vs RDI, fused risk, recent meals.
- Deployed and reachable: Vercel frontend, Render backend, Docker Compose for full-stack local runs.

**Detailed explanation:**
Present the PDF and dashboard as the tangible deliverables — a shareable
artefact a user can download after a single meal photo.

**Speaker notes:**
"Every step you saw live ends in a professional PDF that can be downloaded and
shared — a real artefact for the user, not just a screen."

**Suggested screenshots:** **PDF first page**, **History**, **Trends**, **Dashboard**.

**Timing:** 1:00

---

## Slide 13 — Evaluation & Benchmarking

**Title:** Evaluation & Benchmarking

**Bullet points:**
- **149 pytest tests collected** across 10 files — thresholds, duplicate detection, AI caching, chat, PDF, evaluation, coach, assistant, meal-AI integration.
- Frontend quality gate: `tsc --noEmit` (0 errors) + production build.
- **Benchmark module** (`backend/evaluation/`): per-stage latency with mean/median/p95, memory, cache hit-rate.
- Sample-run numbers: deterministic pipeline **~64 ms total** (disease prediction dominates at ~51 ms); **AI cache hit 63.9% faster** than a miss; PDF generation ~8 ms.
- Artefacts auto-generated: CSV, JSON, matplotlib charts, thesis tables **5.1–5.4** — regenerate with real models / API key to refresh.

**Detailed explanation:**
Present the numbers honestly: the sample run used fast detector/classifier stubs
plus the real XGBoost models, so the **relative ordering** of stages is the
meaningful result. The evaluation module regenerates all tables on demand.

**Speaker notes:**
"The system is tested at unit, integration, and benchmark levels. The evaluation
module generates the thesis tables directly, and the cache benchmark shows a
63.9% latency improvement on hits."

**Suggested screenshots:** `table_5_1_pipeline_runtime.md`, `pipeline_latency.png`, a benchmark CSV from `backend/evaluation/reports/`.

**Timing:** 1:00

---

## Slide 14 — Future Scope

**Title:** Future Scope

**Bullet points:**
- Retrain / fine-tune YOLO and EfficientNet on a larger, region-specific dataset — and document accuracy.
- **GPU inference + model quantisation** for faster, larger deployments (currently CPU-only).
- Add OpenAI / Claude / Ollama / Azure behind the existing `LLMClient` interface.
- Persist chat sessions (Redis) for horizontal scaling.
- Add Alembic migrations, rate limiting, and admin dashboards.
- **Clinically validate** the health score and disease models on real cohorts.
- Estimate **portion size directly from the image** (removes the 100 g assumption).

**Detailed explanation:**
Present future work as a credible roadmap — most items are architecturally
anticipated (pluggable provider factory, ready schema, automated evaluation).

**Speaker notes:**
"The architecture already anticipates most of these: providers are pluggable,
the schema is ready, and evaluation is fully automated — so each item is an
incremental step, not a rewrite."

**Suggested screenshots:** no screenshot — a Now / Next / Later roadmap graphic.

**Timing:** 0:45

---

## Slide 15 — Conclusion & Thank You

**Title:** Conclusion

**Bullet points:**
- A complete, deployable **vision → nutrition → disease-risk → AI-coaching** system.
- **Deterministic, explainable ML core**; safe, **grounded AI layer**.
- **149 tests**, production build, full thesis documentation, automated benchmark suite.
- Reproducible, extensible, and **provider-agnostic**.

**End slide:** *Thank You — Questions?*

**Detailed explanation:**
Summarise the contribution in one breath and invite questions.

**Speaker notes:**
"DietRiskNet shows how a deterministic clinical-analysis core can be safely
enhanced with generative AI — and it is fully reproducible, tested, and
documented. Thank you — I'm happy to take questions."

**Suggested screenshots:** final Dashboard screenshot + QR/link to the repository.

**Timing:** 0:30

---

# Presentation Quick-Reference

| Slide | Topic | Timing |
|---|---|---|
| 1 | Title | 0:15 |
| 2 | Problem | 0:45 |
| 3 | Objectives | 0:45 |
| 4 | Literature Survey | 1:00 |
| 5 | Architecture | 1:00 |
| 6 | Vision pipeline | 1:00 |
| 7 | Nutrition + DCI/NIS | 1:00 |
| 8 | Prediction + Fusion | 1:00 |
| 9 | Rules + AI Dietitian | 1:00 |
| 10 | Chat + Assistant | 1:00 |
| 11 | Nutrition Coach | 1:00 |
| 12 | Results & UI | 1:00 |
| 13 | Evaluation | 1:00 |
| 14 | Future Scope | 0:45 |
| 15 | Conclusion | 0:30 |
| **Total** | | **≈ 15:00** |

---

# Key Numbers to Memorize (for Q&A)

| Item | Value |
|---|---|
| Nutrition database | 1,014 Indian dishes × 11 nutrients |
| Food classes (EfficientNet) | 118 |
| Detection classes (YOLOv8) | 18 |
| Disease-risk models | 4 × XGBoost (diabetes, obesity, hypertension, deficiency) |
| Risk-fusion levels | Low / Moderate / High / Critical (≤ 0.25 / 0.50 / 0.75) |
| DCI thresholds | 0.85 / 0.70 / 0.50 |
| NIS thresholds | 0.2 / 0.4 / 0.6 / 0.8 |
| Duplicate-suppression IoU | 0.6 |
| Rule triggers | sodium > 800 mg · sugar > 15 g · calories > 800 kcal |
| AI cache | SHA-256 context hash, keyed (context_hash, provider) |
| Chat memory | 10-message rolling window |
| Coach analytics | 14-meal window (5-meal pattern window) |
| Backend tests | 149 collected |
| Database tables | 12 |
| Sample pipeline runtime | ~64 ms total (disease prediction ~51 ms) |
| Stack | Next.js 16 · React 19 · FastAPI 0.139 · Python 3.10 · PyTorch (CPU) |
