# DietRiskNet — External Examiner Review

**Project:** DietRiskNet — Vision-Language-Based Food Recognition and Personalized
Disease-Risk-Aware Dietary Recommendation Using Longitudinal Meal Analysis

**Reviewer:** External University Examiner (independent assessment)

**Date of review:** 2026-07-31

**Basis of review:** Full examination of the repository — backend source
(`backend/`), frontend (`frontend/`), ML models and configs
(`backend/trained_models/`), nutrition database, database models, test suite,
evaluation/benchmark reports (`backend/evaluation/reports/`), deployment files
(`docker-compose.yml`, `render.yaml`, Dockerfiles), and all documentation
(`docs/thesis/`, `docs/final/`, `README.md`). Where a claim could be verified
against source, it was.

---

## 1. Overview

DietRiskNet is a complete, deployable full-stack medical-AI application. A user
photographs a meal; YOLOv8 detects food regions, EfficientNet-B3 classifies
each crop into 118 Indian dishes, a 1,014-dish nutrition database provides
per-item nutrition, deterministic DCI/NIS indices are computed, four XGBoost
models predict disease risk, a weighted fusion produces a single risk level,
and a rule engine plus a grounded, fail-safe Gemini AI layer explain and
personalise the advice. The result is persisted, visualised across a
dashboard/trends/history UI, and exportable as a professional PDF.

The project is **substantially above the bar for a final-year project.** It is a
real, running, tested, deployable system with professional documentation. The
limitations are honest and mostly relate to the fact that the ML models are
pre-trained and treated as black boxes, and to a handful of production-hardening
gaps (rate limiting, CI, chat persistence). None of these prevent academic
submission.

---

## 2. Dimension scores

| # | Dimension | Score /10 | Weight | Weighted |
|---|---|---|---|---|
| 1 | Innovation | 7.5 | 0.10 | 0.75 |
| 2 | Machine Learning | 6.5 | 0.15 | 0.975 |
| 3 | Software Engineering | 8.5 | 0.15 | 1.275 |
| 4 | Architecture | 9.0 | 0.15 | 1.350 |
| 5 | UI | 8.5 | 0.05 | 0.425 |
| 6 | Testing | 7.5 | 0.10 | 0.750 |
| 7 | Security | 7.0 | 0.10 | 0.700 |
| 8 | Documentation | 9.0 | 0.10 | 0.900 |
| 9 | Deployment | 8.0 | 0.05 | 0.400 |
| 10 | Scalability | 5.5 | 0.025 | 0.138 |
| 11 | Maintainability | 8.0 | 0.05 | 0.400 |
| | **Weighted overall** | | **1.00** | **8.1 / 10** |

**Overall grade estimate: A− (High Distinction / Excellent).**
Band justification: 8.1/10 places the work in the 75–84% "Excellent" range —
originality in the integration, very strong engineering and documentation,
with the primary deductions coming from the unvalidated, pre-trained ML models
and production-hardening gaps.

---

## 3. Detailed assessment by dimension

### 3.1 Innovation — 7.5/10

- The novelty is **integration**, not new models: end-to-end food vision →
  regional nutrition → disease-risk ML → grounded conversational coaching in
  one deployable system. This is a legitimate and well-executed contribution
  for a capstone, and it directly addresses a real gap (region-specific food
  recognition + clinical-risk framing + safe AI).
- Genuine design improvements worth recognising:
  - **Deterministic, order-independent threshold classifier** replacing
    interval-range classification (which was ambiguous at shared boundaries and
    dependent on dict iteration order). This is a small but real algorithmic
    contribution with mathematical justification ([classification.py](backend/services/classification.py)).
  - **Fail-safe AI architecture**: the LLM can never break the pipeline;
    `ai_dietitian` is nullable and the rule engine always stands.
  - **Provider-agnostic LLM abstraction** with a **persistent SHA-256
    context-hash cache** so identical contexts never re-invoke the LLM.
  - **Longitudinal Nutrition Coach** built entirely from deterministic
    analytics over stored meal history (patterns, smart goals with 0–1
    progress), with the LLM only narrating verified numbers.
- Deduction: no novel algorithm, and the innovation is at the system level
  rather than the model level — expected for this scope, but it caps the
  score.

### 3.2 Machine Learning — 6.5/10

- The **pipeline design is sound and correctly implemented**: YOLOv8 (18
  detection classes) → per-class IoU 0.6 duplicate suppression → EfficientNet-B3
  (118 classes, B0 fallback, crop sizes 300/224) → nutrition lookup
  (exact → alias → normalised → fuzzy) → DCI (1−CV over a 7-day window, macro
  fallback) → NIS (mean relative RDI deviation) → 4 XGBoost models → weighted
  fusion.
- The deterministic DCI/NIS design is a genuine strength (reproducible,
  explainable, boundary-safe).
- Significant deductions:
  1. **No model validation is reported.** There are no accuracy,
     precision/recall, F1, or confusion-matrix figures for the YOLOv8,
     EfficientNet, or XGBoost models anywhere in the thesis or evaluation
     module — only **latency/memory** benchmarks. For an ML project, this is
     the single largest gap.
  2. **The vision benchmarks used stub detector/classifier** (honestly
     disclosed), so even the presented numbers are not production figures.
  3. **Several XGBoost features are hardcoded constants** (verified in
     [prediction_service.py](backend/services/prediction_service.py)):
     hypertension's stress/sleep/medication/exercise/smoking are fixed; the
     diabetes model estimates HbA1c and glucose heuristically; the deficiency
     model fixes haemoglobin at 14.0. This materially limits the real-world
     validity of the risk outputs and should be stated explicitly.
  4. The obesity model is **multiclass** (risk = Σ of overweight+obese class
     probabilities) and does not use BMI — undocumented and easy to
     misread as binary logistic regression.
- These do not indicate implementation errors; they indicate a need to
  **scope and state the ML claims honestly** and to add a validation section.

### 3.3 Software Engineering — 8.5/10

- Clean, consistent codebase: typed Pydantic schemas, thin route layer,
  service layer with module-level singletons, centralised logging, typed
  exceptions (`LLMProviderError` family), and clear file organisation.
- Strong auth engineering: bcrypt hashing (via passlib), JWT access/refresh
  tokens with **unique `jti`**, a token-**type** claim (access vs refresh
  separation), **database-stored refresh tokens with revocation** (`is_revoked`),
  audit-logging on key actions.
- Thoughtful details: insecure-default SECRET_KEY detection with runtime
  warning; self-healing frontend API fallback; UUID upload filenames;
  AI caching with `prompt_version` cache-busting; active model unloading to
  fit a 512 MB Render instance.
- Minor deductions: a bcrypt/passlib **monkey-patch** in
  [auth_utils.py](backend/utils/auth_utils.py) (works but fragile); duplicated
  upload-validation code in [meal.py](backend/routes/meal.py); a few Pydantic
  v2 deprecation warnings; no migrations tooling.

### 3.4 Architecture — 9.0/10

- Excellent separation of concerns: **deterministic ML core vs. AI
  explanation layer** is the key architectural idea and it is executed
  consistently across routes, services, models, and the schema.
- Clean three-tier design (Next.js frontend → FastAPI → SQLAlchemy DB), a
  normalized 12-table relational schema (verified against
  [models.py](backend/database/models.py) and
  [ai_dietitian.py](backend/models/ai_dietitian.py)) with cascading deletes and
  purposeful composite indexes.
- Provider abstraction (`LLMClient` interface + factory) makes the AI layer
  swappable (Gemini now; OpenAI/Claude/Ollama/Azure by adding one module).
- Memory-conscious design (single-worker CPU inference, lazy loading, model
  unloading) — appropriate for the free-tier deployment target.
- The architecture is genuinely production-shaped, which is rare for a
  capstone.

### 3.5 UI — 8.5/10

- Polished, cohesive dark clinical theme; consistent design language
  (charcoal, blue/emerald accents); Framer Motion transitions; responsive
  layout with a collapsible sidebar.
- Feature-complete screens: landing, auth, profile, upload, analysis
  (bounding-box overlays + per-segment cards), predictions (four risk gauges +
  fused score), recommendations, coach dashboard (stat tiles, pattern insights,
  smart-goal progress bars), trends (7/14/30-day Recharts), history, research,
  about.
- AI surfaces are well integrated (AI Dietitian card, meal chat panel, coach
  chat) with suggested-prompt chips and empty/loading/error states.
- Minor: dense text on some cards; a few `text-[10px]`-scale labels push
  readability limits.

### 3.6 Testing — 7.5/10

- **149 tests collected** across 10 files (verified via `pytest --collect-only`)
  covering thresholds, duplicate detection, AI caching, meal chat, nutrition
  assistant, coach analytics, meal-AI integration, PDF report, and evaluation.
- Frontend gates: `tsc --noEmit` (0 errors) and production build.
- Deductions:
  - **No dedicated auth/security test file** (no coverage for JWT flows,
    token refresh/revocation, registration validation).
  - **No CI pipeline** — tests exist but nothing enforces them.
  - The evaluation benchmark ran the pipeline on **n = 2** iterations, making
    the reported median/p95 statistically weak (n should be ≥ 20–30).
  - The thesis's "122 passed" figure is stale (actual collected total: 149).

### 3.7 Security — 7.0/10

Strengths (verified): bcrypt password hashing; JWT with `jti` + type claims;
refresh tokens stored and revocable in the DB; audit logging; upload extension
whitelist + UUID filenames (no path traversal); restricted CORS (localhost +
`*.vercel.app` regex); fail-safe AI (no PII/bounding boxes/images sent to the
LLM — only display-safe structured fields); `.env`/`.db`/uploads excluded from
git; runtime warning on insecure SECRET_KEY; input length/type validation via
Pydantic (password min 6, `EmailStr`).

Weaknesses:
1. **No rate limiting** on auth or inference endpoints (brute-force /
   cost-amplification risk).
2. **No upload size limit** and only extension-based validation (no
   magic-byte content check) — a crafted file could consume disk/memory.
3. **No CSRF protection** on the frontend (mitigated by a same-site/stateless
   JWT-in-localStorage model, but worth stating).
4. Password policy is minimal (min length 6, no complexity rules, no
   breach/attempt throttling).
5. No automated security tests (no auth fuzz, no malformed-token tests).

### 3.8 Documentation — 9.0/10

- Exceptionally well documented: a 14-chapter thesis (architecture, sequence
  diagrams, DFD, component diagram, ER diagram, methodology, experimental
  setup, results, discussion, conclusion, deployment, user manual, developer
  guide), a demo script, a 100-question viva Q&A bank, an API reference, a
  deployment guide, an evaluation module that auto-generates thesis-ready
  tables, and a clear README/HOW-TO-RUN.
- Deductions: the thesis has **no references/bibliography and no inline
  citations**; it contains two factual slips (risk-fusion levels omit
  "Critical"; the "122 tests" count is stale); figure/table numbering needs a
  consistency pass (addressed in the companion `04_THESIS_REVIEW.md`).

### 3.9 Deployment — 8.0/10

- Working, verified deployment story: `docker-compose.yml` (PostgreSQL 15 +
  backend + frontend with volume mounts for models/uploads),
  `backend/Dockerfile` (python:3.10-slim with OpenCV system deps),
  `render.yaml` (free-tier web + DB, auto-generated `SECRET_KEY`), and a
  Vercel-deployed frontend with self-healing API fallback.
- SQLite→PostgreSQL parity is handled through SQLAlchemy.
- Deductions: no CI/CD pipeline; `docker-compose` ships a dev SECRET_KEY (with
  an explicit warning comment); deployment is manual.

### 3.10 Scalability — 5.5/10

- Chat/session state is **in-memory only** (256-session cap, idle-TTL
  eviction) — lost on restart, no horizontal scaling.
- Single uvicorn worker, CPU-only inference; no queueing/batching for ML
  inference; no API response caching (beyond the AI cache); no horizontal DB
  read replicas.
- This is an acknowledged, documented limitation and is **reasonable for a
  capstone**, but it is the weakest dimension.

### 3.11 Maintainability — 8.0/10

- Consistent conventions, well-named modules, centralised logging, typed
  schemas, documented developer guide (adding providers/models/prompts),
  and a solid test safety net make the codebase genuinely maintainable.
- Deductions: the bcrypt monkey-patch; duplicated upload validation; no
  migrations; some magic numbers in `prediction_service.py` (hardcoded
  feature values) are undocumented.

---

## 4. Strengths

1. **Complete end-to-end product** — a single deployable system from meal
   photo to disease-risk report and AI coaching, not a collection of notebooks.
2. **Principled architecture** — deterministic clinical core separated from a
   fail-safe, provider-agnostic AI layer; the best single idea in the project.
3. **Deterministic, order-independent DCI/NIS classifier** — a real, provable
   improvement over naive interval ranges.
4. **Security baseline well above capstone norm** — bcrypt, JWT `jti`/type
   claims, revocable refresh tokens, audit logging, restricted CORS, safe
   upload handling, fail-safe LLM, git hygiene.
5. **Excellent testing breadth** — 149 tests across 10 focused suites, plus
   frontend type/build gates.
6. **Professional, feature-complete UI** with consistent design language,
   visualisations, and AI surfaces.
7. **First-class documentation** — thesis, demo script, viva Q&A bank, API
   reference, and an evaluation module that generates thesis-ready tables.
8. **Real deployment story** — Docker Compose, Render blueprint, Vercel
   frontend, SQLite→PostgreSQL parity, memory-conscious for a 512 MB target.
9. **Honest evaluation culture** — stub-based vision benchmarks are disclosed
   rather than hidden; limitations are candidly documented.
10. **AI caching + longitudinal coach analytics** — genuine engineering depth
    beyond the core ML pipeline.

---

## 5. Weaknesses

1. **No reported model validation** — no accuracy/precision/recall for any of
   the five ML models; the only numbers are latency/memory.
2. **Several XGBoost features are hardcoded constants** (hypertension
   stress/sleep/exercise, diabetes HbA1c/glucose heuristics, deficiency
   haemoglobin), limiting the real-world validity of risk outputs and
   under-documented in the thesis.
3. **Vision benchmarks used stubs**, so presented pipeline timings are not
   production figures (honestly disclosed, but still a gap).
4. **No rate limiting, no upload size limit, no magic-byte file validation.**
5. **No dedicated auth/security tests and no CI pipeline** to enforce the
   test suite.
6. **In-memory chat sessions** — lost on restart, no horizontal scaling.
7. **No Alembic migrations**; schema changes rely on `create_all`.
8. **Thesis gaps**: no references/citations; stale "122 tests" count; fusion
   levels described as three (code has four incl. "Critical").
9. **Portion-size assumption** — serving weights are static defaults, not
   estimated from the image; nutrition figures inherit this uncertainty.
10. **Single-worker, CPU-only inference**; no GPU path or queueing.

---

## 6. Optional improvements (not required for submission)

**High impact:**
1. Add a validation section to the thesis and evaluation module: report
   accuracy/precision/recall (or at least a held-out-set sanity check) for the
   detector, classifier, and the four XGBoost models.
2. Document the XGBoost feature engineering honestly (hardcoded inputs,
   multiclass obesity, metre-height input) in the thesis.
3. Add rate limiting (e.g. `slowapi`) on auth and `/analyze-meal`.
4. Add upload size limits and content verification (PIL/magic-byte check).

**Medium impact:**
5. Add a GitHub Actions CI pipeline (pytest + `tsc --noEmit` + build).
6. Add an auth/security test suite.
7. Raise benchmark iterations to ≥ 20 and state sample size in the tables.
8. Introduce Alembic migrations.
9. Persist chat sessions to the DB (or Redis) with a bounded window.

**Low impact / polish:**
10. Add structured logging / health & readiness endpoints.
11. Add GPU/quantisation toggle (env-flag) for faster inference.
12. Add portion-size estimation from the image (larger project, noted in
    future work).
13. Clean up the bcrypt monkey-patch and de-duplicate upload validation.
14. Fix the thesis's factual slips (test count, fusion levels) and add a
    References section.

---

## 7. Conclusion

As external examiner, I find DietRiskNet to be an **impressive, complete, and
honest engineering project**. It delivers a working end-to-end medical-AI
system with a genuinely well-designed architecture (deterministic core + safe
AI layer), strong security and testing for a capstone, a polished UI, and
documentation of unusual depth. The weaknesses are real but are
**scope-honest** — pre-trained models without reported validation, a few
hardcoded feature inputs, and production-hardening gaps (rate limiting, CI,
chat persistence) — and none undermine the integrity of the submission.

The two factual slips found in the thesis documentation (risk-fusion levels
and the automated test count) are documentation corrections, not defects in
the implementation, and should be applied before final printing.

**Overall grade estimate: 8.1/10 — A− (High Distinction).**

**Ready for Academic Submission** — *with the minor documentation corrections
(listed in §6.14 and in the companion `docs/final/04_THESIS_REVIEW.md`) applied
before final submission.*
